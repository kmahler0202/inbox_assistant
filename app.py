from flask import Flask, request, jsonify
import openai
import os

app = Flask(__name__)

# Set your key here or use environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get("message", "")

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_message}
        ],
        temperature=0.5
    )

    reply = response.choices[0].message.content.strip()
    return jsonify({"reply": reply})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
