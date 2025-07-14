from flask import Flask, request, jsonify
from openai import OpenAI
from classifier import classify_email
from summarizer import summarize_email
from smart_reply import draft_smart_reply
from digest import build_digest
from extract import extract_action_items
import os

import base64
import requests

import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from flask import current_app

import redis

from datetime import datetime

r = redis.from_url(os.environ['REDIS_URL'], decode_responses=True)

app = Flask(__name__)

# PUB/SUB TOPIC NAME BELOW:
# projects/email-organizer-461719/topics/gmail-notify

# Render URL below
# https://inbox-assistant-x5uk.onrender.com

# Set your key here or use environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def index():
    return 'Inbox Assistant Backend Is Running...'

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")
    print("user_message raw:", user_message)
    print("type:", type(user_message))

    # Just to be safe, convert to string in case it's a number or object
    user_message = str(user_message)

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant inside of an inbox."},
            {"role": "user", "content": user_message}
        ]
    )

    reply = response.choices[0].message.content.strip()
    return jsonify({"reply": reply})

@app.route('/classify', methods=['POST'])
def classify():
    data = request.get_json()
    subject = data.get("subject", "")
    snippet = data.get("snippet", "")

    subject = str(subject)
    snippet = str(snippet)
    
    label = classify_email(subject, snippet)
    return jsonify({"label": label})

@app.route('/start_watch')
def start_watch():
    
    try:
        # Read the secret file contents from disk
        with open('/etc/secrets/GMAIL_TOKEN_JSON') as f:
            creds_data = json.load(f)

        creds = Credentials.from_authorized_user_info(creds_data)

        service = build('gmail', 'v1', credentials=creds)

        request = {
            'labelIds': ['INBOX', 'SENT'],
            'topicName': 'projects/email-organizer-461719/topics/gmail-notify',
            'labelFilterBehavior': 'INCLUDE'
        }

        response = service.users().watch(userId='me', body=request).execute()
        history_id = response.get('historyId')

        r.set("gmail:history_id", str(history_id))

        print("Watch registered:", response,)

        return jsonify(response)

    except Exception as e:
        return f"Error: {e}", 500
    

@app.route('/gmail_webhook', methods=['POST'])
def gmail_webhook():
    print("Entered webhook", flush=True)
    envelope = request.get_json()
    if not envelope or 'message' not in envelope:
        return 'Invalid message format', 400

    status_messages = ["📩 Push notification received."]
    try:
        # Load Gmail credentials
        with open('/etc/secrets/GMAIL_TOKEN_JSON') as f:
            creds_data = json.load(f)
        creds = Credentials.from_authorized_user_info(creds_data)
        service = build('gmail', 'v1', credentials=creds)

        # Read last saved historyId
        saved_history_id = r.get("gmail:history_id")
        if not saved_history_id:
            return "⚠️ No historyId stored in Redis yet.", 400

        # Get history since last known point
        history = service.users().history().list(
            userId='me',
            startHistoryId=saved_history_id,
            historyTypes=['messageAdded']
        ).execute()

        # Get new highest historyId
        if 'historyId' in history:
            r.set("gmail:history_id", str(history['historyId']))

        new_messages = []
        for h in history.get('history', []):
            for m in h.get('messagesAdded', []):
                msg = m.get('message')
                if msg and msg.get('id'):
                    new_messages.append(msg['id'])

        if not new_messages:
            status_messages.append("📭 No new messages to process.")
            print('\n'.join(status_messages))
            return '\n'.join(status_messages), 200

        for msg_id in new_messages:
            msg_data = service.users().messages().get(
                userId='me', id=msg_id, format='metadata', metadataHeaders=['Subject']
            ).execute()

            labels = msg_data.get('labelIds', [])

            # ✅ Handle sent emails for follow-up tracking
            if 'SENT' in labels:
                sent_time = int(msg_data['internalDate'])
                thread_id = msg_data['threadId']
                subject = next((h['value'] for h in msg_data['payload']['headers'] if h['name'] == 'Subject'), '')

                r.hset(f"sent_followups:{thread_id}", mapping={
                    "subject": subject,
                    "sent_time": sent_time
                })

                status_messages.append(f"📤 Tracked SENT email for follow-up: {subject}")
                continue  # Skip rest of loop for sent messages

            subject = next((h['value'] for h in msg_data['payload']['headers'] if h['name'] == 'Subject'), '')
            snippet = msg_data.get('snippet', '')

            status_messages.append(f"📬 New message ID: {msg_id}")
            status_messages.append(f"✉️ Subject: {subject}")

            classify_response = requests.post(
                'https://inbox-assistant-x5uk.onrender.com/classify',
                json={"subject": subject, "snippet": snippet}
            )
            label = classify_response.json().get('label', 'Other')
            status_messages.append(f"🏷️ Message classified as: {label}")

            

            # Label handling
            all_labels = service.users().labels().list(userId='me').execute().get('labels', [])
            label_ids = {lbl['name']: lbl['id'] for lbl in all_labels}
            if label not in label_ids:
                new_label = service.users().labels().create(userId='me', body={"name": label}).execute()
                label_ids[label] = new_label['id']
                status_messages.append(f"🆕 Created new label: {label}")

            modified_body = {
                "addLabelIds": [label_ids[label]],
                "removeLabelIds": []
            }

            if label == "Promotions":
                modified_body["removeLabelIds"].append("INBOX")
            else:
                full_msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                body_data = get_email_body(full_msg_data)
                action_items = extract_action_items(subject, body_data)

                if action_items:
                    status_messages.append(f"📌 Action Items Found: {len(action_items)} items.")
                    for item in action_items:
                        status_messages.append(f"➡️ {item}")

                # Optional: track stats
                    increment_stat(r.get('linked_gmail_user'), 'actionItemsExtracted')

                    # Optional: store action items in Redis list
                    for item in action_items:
                            r.rpush(f"action_items:{msg_id}", item)

                    existing_items = r.hget("action_items_global", msg_id)
                    if existing_items:
                        items = json.loads(existing_items) + action_items
                    else:
                        items = action_items
                    r.hset("action_items_global", msg_id, json.dumps(items))

            service.users().messages().modify(
                userId='me',
                id=msg_id,
                body=modified_body
            ).execute()

            status_messages.append("✅ Label applied")

            # STAT TRACKING TO GO HERE'

            increment_stat(r.get('linked_gmail_user'), 'emailsReceived')
            increment_stat(r.get('linked_gmail_user'), 'emailsSorted')

        print('\n'.join(status_messages))
        return '\n'.join(status_messages), 200
    
    

    except Exception as e:
        status_messages.append(f"❌ Error: {str(e)}")
        print('\n'.join(status_messages))
        return '\n'.join(status_messages), 500
    
@app.route('/get_followups', methods=['GET'])
def get_followups():
    from datetime import datetime, timedelta
    with open('/etc/secrets/GMAIL_TOKEN_JSON') as f:
        creds_data = json.load(f)
    creds = Credentials.from_authorized_user_info(creds_data)
    service = build('gmail', 'v1', credentials=creds)

    now = datetime.utcnow()
    followups = []
    keys = r.keys("sent_followups:*")
    for key in keys:
        thread_id = key.split(":")[1]
        data = r.hgetall(key)
        sent_time = datetime.utcfromtimestamp(int(data.get('sent_time')) / 1000)
        if (now - sent_time).days < 2:
            continue  # skip recent emails
        
        thread = service.users().threads().get(userId='me', id=thread_id).execute()
        messages = thread.get('messages', [])
        if len(messages) <= 1:
            followups.append({
                "subject": data.get("subject"),
                "thread_id": thread_id,
                "days_since_sent": (now - sent_time).days
            })

    return jsonify(followups)

@app.route('/send_followup', methods=['POST'])
def send_followup():
    data = request.get_json()
    thread_id = data.get('thread_id')
    draft = data.get('draft')

    with open('/etc/secrets/GMAIL_TOKEN_JSON') as f:
        creds_data = json.load(f)
    creds = Credentials.from_authorized_user_info(creds_data)
    service = build('gmail', 'v1', credentials=creds)

    message = {
        "raw": base64.urlsafe_b64encode(
            f"Subject: Following up\n\n{draft}".encode('utf-8')
        ).decode('utf-8'),
        "threadId": thread_id
    }

    sent = service.users().messages().send(userId='me', body=message).execute()
    return jsonify({"status": "sent", "id": sent.get("id")})


@app.route('/save_settings', methods=['POST'])
def save_settings():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400

    # Convert all values to strings before saving to Redis
    r.hset(f"user:{email}:settings", mapping={
        "autoSortEnabled": str(to_bool(data.get("autoSortEnabled"))),
        "summarizerEnabled": str(to_bool(data.get("summarizerEnabled"))),
        "digestEnabled": str(to_bool(data.get("digestEnabled"))),
        "digestTime": str(data.get("digestTime", "")),
        "actionItemsEnabled": str(to_bool(data.get("actionItemsEnabled"))),
        "draftRepliesEnabled": str(to_bool(data.get("draftRepliesEnabled"))),
        "followUpEnabled": str(to_bool(data.get("followUpEnabled"))),
        "chatAssistantEnabled": str(to_bool(data.get("chatAssistantEnabled"))),
        "sortingLabels": json.dumps(data.get("sortingLabels", [])),
        "customLabels": json.dumps(data.get("customLabels", []))
    })


    # Mark user as onboarded
    r.set(f"user:{email}:onboarded", "true")

    r.set("linked_gmail_user", email)

    print('User saved settings.', flush=True)

    return jsonify({"status": "ok"})

@app.route("/is_onboarded", methods=["POST"])
def is_onboarded():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "No email provided"}), 400

    status = r.get(f"user:{email}:onboarded")
    return jsonify({"onboarded": status == "true"})


@app.route('/get_settings', methods=['POST'])
def get_settings():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400

    settings = r.hgetall(f"user:{email}:settings")
    print('Got Settings', flush=True)
    
    for key in settings:
        val = settings[key]
        if val == "True":
            settings[key] = True
        elif val == "False":
            settings[key] = False
        else:
            try:
                settings[key] = json.loads(val)
            except:
                pass  # leave as string

    return jsonify(settings)


# debugging route to show whats in the database
@app.route('/debug/redis')
def debug_redis():

    try:
        r.ping()
        print("Connected to Redis Succesfully", flush=True)
    except Exception as e:
        print('Redis connection failed', flush=True)



    keys = r.keys("*")
    data = {}

    for key in keys:
        try:
            key_type = r.type(key)
            if key_type == 'string':
                data[key] = r.get(key)
            elif key_type == 'list':
                data[key] = r.lrange(key, 0, -1)
            elif key_type == 'hash':
                data[key] = r.hgetall(key)
            elif key_type == 'set':
                data[key] = list(r.smembers(key))
            else:
                data[key] = f"(unhandled type: {key_type})"
        except Exception as e:
            data[key] = f"(error: {str(e)})"

    return jsonify(data)

@app.route("/get_stats", methods=["POST"])
def get_stats():
    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400

    key = f"stats:{email}:since_last_digest"
    raw = r.hgetall(key)

    stats = {
        "emailsReceived": int(raw.get("emailsReceived", 0)),
        "emailsSorted": int(raw.get("emailsSorted", 0)),
        "summariesGenerated": int(raw.get("summariesGenerated", 0)),
        "actionItemsExtracted": int(raw.get("actionItemsExtracted", 0)),
    }

    return jsonify(stats)

@app.route('/summarize', methods=['POST'])
def summarize():
    data = request.get_json()
    subject = str(data.get("subject", ""))
    body = str(data.get("body", ""))
    email = data.get("email")
    
    summary = summarize_email(subject, body)

    increment_stat(email, 'summariesGenerated')

    return jsonify({"summary": summary})

@app.route('/daily_digest', methods=['POST'])
def daily_digest():
    from datetime import datetime, timedelta

    data = request.get_json()
    email = data.get("email")
    if not email:
        return jsonify({"error": "Missing email"}), 400

    last_digest_time_str = r.get(f"user:{email}:last_digest_time")
    if last_digest_time_str:
        last_digest_time = datetime.fromisoformat(last_digest_time_str)
    else:
        last_digest_time = datetime.utcnow() - timedelta(hours=24)

    with open('/etc/secrets/GMAIL_TOKEN_JSON') as f:
        creds_data = json.load(f)
    creds = Credentials.from_authorized_user_info(creds_data)
    service = build('gmail', 'v1', credentials=creds)

    # Get recent messages
    results = service.users().messages().list(
        userId='me',
        q=f"after:{int(last_digest_time.timestamp())}",
        labelIds=['INBOX']
    ).execute()

    message_ids = [msg['id'] for msg in results.get('messages', [])]

    digest = build_digest(email, service, message_ids)

    # Reset the stat timestamp
    r.set(f"user:{email}:last_digest_time", digest["timestamp"])
    r.delete(f"stats:{email}:since_last_digest")

    return jsonify(digest)


@app.route('/draft_reply', methods=['POST'])
def draft_reply():
    data = request.get_json()
    subject = str(data.get("subject", ""))
    body = str(data.get("body", ""))

    draft = draft_smart_reply(subject, body)
    return jsonify({"draft": draft})

@app.route('/get_all_action_items', methods=['GET'])
def get_all_action_items():
    all_items = r.hgetall("action_items_global")
    result = []
    for msg_id, items_json in all_items.items():
        for item in json.loads(items_json):
            result.append({"message_id": msg_id, "item": item})
    return jsonify({"items": result})

@app.route('/clear_action_item', methods=['POST'])
def clear_action_item():
    data = request.get_json()
    msg_id = data.get('message_id')
    item = data.get('item')
    items = json.loads(r.hget("action_items_global", msg_id) or '[]')
    items = [i for i in items if i != item]
    if items:
        r.hset("action_items_global", msg_id, json.dumps(items))
    else:
        r.hdel("action_items_global", msg_id)
    return jsonify({"status": "done"})


def get_email_body(message):
    try:
        parts = message.get('payload', {}).get('parts', [])
        for part in parts:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data')
                if data:
                    from base64 import urlsafe_b64decode
                    return urlsafe_b64decode(data).decode('utf-8')
        # fallback
        return message.get('snippet', '')
    except Exception:
        return message.get('snippet', '')

def to_bool(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, list):  # checkbox fields like ["enabled"]
        return "enabled" in val
    if isinstance(val, str):
        return val.strip().lower() in ["true", "1", "yes", "on", "enabled"]
    return bool(val)

def increment_stat(email, field):
    today_key = f"stats:{email}:{datetime.utcnow().date()}"
    digest_key = f"stats:{email}:since_last_digest"
    r.hincrby(today_key, field, 1)
    r.hincrby(digest_key, field, 1)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
