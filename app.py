from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
