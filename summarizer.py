from openai import OpenAI
import os

MAX_SNIPPET_LEN = 1000
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarize_email(subject, body):
    body = body[:MAX_SNIPPET_LEN]

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are an assistant that summarizes emails clearly and concisely."},
            {"role": "user", "content": f"Subject: {subject}\n\nBody: {body}\n\nSummarize this email."}
        ]
    )
    return response.choices[0].message.content.strip()
