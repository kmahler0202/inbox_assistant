from flask import Flask, request, jsonify
from openai import OpenAI
from classifier import classify_email
import os

import base64
import requests

import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from flask import current_app



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
            'labelIds': ['INBOX'],
            'topicName': 'projects/email-organizer-461719/topics/gmail-notify',
            'labelFilterBehavior': 'INCLUDE'
        }

        response = service.users().watch(userId='me', body=request).execute()
        history_id = response.get('historyId')
        print("Watch registered:", response)

        return jsonify(response)

    except Exception as e:
        return f"Error: {e}", 500
    
@app.route('/gmail_webhook', methods=['POST'])
def gmail_webhook():
    print("Entered webhook", flush=True)
    envelope = request.get_json()
    if not envelope or 'message' not in envelope:
        return 'Invalid message format', 400

    message = envelope['message']
    data = message.get('data')
    if not data:
        print('\n'.join(status_messages))
        return 'No data in message', 204

    status_messages = ["📩 Push notification received."]



    try:
        with open('/etc/secrets/GMAIL_TOKEN_JSON') as f:
            creds_data = json.load(f)
        creds = Credentials.from_authorized_user_info(creds_data)
        service = build('gmail', 'v1', credentials=creds)

        # Get the most recent message in the INBOX
        result = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=1).execute()
        messages = result.get('messages', [])

        if not messages:
            status_messages.append("⚠️ No new messages found.")
            print('\n'.join(status_messages))
            return '\n'.join(status_messages), 200

        msg_id = messages[0]['id']

        msg_data = service.users().messages().get(
            userId='me', id=msg_id, format='metadata', metadataHeaders=['Subject']
        ).execute()

        subject = next((h['value'] for h in msg_data['payload']['headers'] if h['name'] == 'Subject'), '')
        snippet = msg_data.get('snippet', '')
        status_messages.append(f"📬 Processing message ID: {msg_id}")
        status_messages.append(f"✉️ Subject: {subject}")



        # Call classifier
        classify_response = requests.post(
            'https://inbox-assistant-x5uk.onrender.com/classify',
            json={"subject": subject, "snippet": snippet}
        )

        label = classify_response.json().get('label', 'Other')
        status_messages.append(f"🏷️ Message classified as: {label}")

        # Add label to Gmail
        all_labels = service.users().labels().list(userId='me').execute().get('labels', [])
        label_ids = {lbl['name']: lbl['id'] for lbl in all_labels}
        if label not in label_ids:
            new_label = service.users().labels().create(userId='me', body={"name": label}).execute()
            label_ids[label] = new_label['id']
            status_messages.append(f"➕ Created new label: {label}")

        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={"addLabelIds": [label_ids[label]]}
        ).execute()

        status_messages.append("✅ Label applied")
        print('\n'.join(status_messages))
        return '\n'.join(status_messages), 200

    except Exception as e:
        status_messages.append(f"❌ Error: {str(e)}")
        # TEMPORARY DEBUG PRINT — so it shows in Render logs
        print('\n'.join(status_messages))
        return '\n'.join(status_messages), 500




    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
