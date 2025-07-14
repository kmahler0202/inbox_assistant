from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def draft_smart_reply(subject, body):
    reply_prompt = f"""You are a helpful email assistant. Your job is to write a draft reply to the following email. The reply should be polite, relevant, and concise.

Subject: {subject}

Body: {body}

Draft a suitable reply:"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You help users quickly draft email replies."},
            {"role": "user", "content": reply_prompt}
        ]
    )

    draft = response.choices[0].message.content.strip()
    return draft
