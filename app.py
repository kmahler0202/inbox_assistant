from flask import Flask, request, jsonify
from openai import OpenAI
from classifier import classify_email
import os

import base64

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
            'topicName': 'projects/email-organizer-461719/topics/gmail-notify'
        }

        response = service.users().watch(userId='me', body=request).execute()
        print("Watch registered:", response)
        return jsonify(response)

    except Exception as e:
        return f"Error: {e}", 500
    
@app.route('/gmail_webhook', methods=['POST'])
def gmail_webhook():
    envelope = request.get_json()

    if not envelope or 'message' not in envelope:
        return 'Invalid Pub/Sub message format', 400

    # Decode base64 message
    pubsub_message = envelope['message']
    data = pubsub_message.get('data')
    if not data:
        return 'No data in message', 204

    decoded_data = base64.b64decode(data).decode('utf-8')
    print(f"✅ Received push: {decoded_data}")

    # Load Gmail credentials from secret file
    try:
        with open('/etc/secrets/GMAIL_TOKEN_JSON') as f:
            creds_data = json.load(f)
        creds = Credentials.from_authorized_user_info(creds_data)
        service = build('gmail', 'v1', credentials=creds)

        # Step 1: List unread messages
        messages_response = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
        messages = messages_response.get('messages', [])

        if not messages:
            print("No new unread messages.")
            return "No new messages", 200

        # Step 2: Get the most recent message
        msg_id = messages[0]['id']
        full_message = service.users().messages().get(userId='me', id=msg_id, format='metadata', metadataHeaders=['Subject']).execute()

        subject = next((h['value'] for h in full_message['payload']['headers'] if h['name'] == 'Subject'), '')
        snippet = full_message.get('snippet', '')

        print(f" New message: {subject[:50]}")

        # Step 3: Call classifier
        import requests
        classify_response = requests.post(
            'https://inbox-assistant-x5uk.onrender.com/classify',  
            json={"subject": subject, "snippet": snippet}
        )
        label = classify_response.json().get('label', 'Other')
        print(f" Classified as: {label}")

        # Step 4: Apply label in Gmail
        # Create label if it doesn’t exist
        all_labels = service.users().labels().list(userId='me').execute().get('labels', [])
        label_ids = {lbl['name']: lbl['id'] for lbl in all_labels}
        if label not in label_ids:
            new_label = service.users().labels().create(userId='me', body={"name": label}).execute()
            label_ids[label] = new_label['id']

        # Apply label and mark as read
        service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={"addLabelIds": [label_ids[label]], "removeLabelIds": ["UNREAD"]}
        ).execute()

        return f"Labeled email '{subject[:40]}' as {label}", 200

    except Exception as e:
        print(f" Error in webhook: {e}")
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
