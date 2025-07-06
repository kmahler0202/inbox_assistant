from flask import Flask, request, jsonify
from openai import OpenAI
from classifier import classify_email
import os

import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from flask import current_app

app = Flask(__name__)

# PUB/SUB TOPIC NAME BELOW:
# projects/email-organizer-461719/topics/gmail-notify

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
        creds_data = json.loads(os.environ['GMAIL_TOKEN_JSON'])
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
        current_app.logger.error(f"Watch registration failed: {e}")
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
