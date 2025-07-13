from datetime import datetime
from classifier import classify_email
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_digest(email, service, message_ids):
    label_counts = {}
    action_items = []

    for msg_id in message_ids:
        msg_data = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        snippet = msg_data.get('snippet', '')
        subject = next((h['value'] for h in msg_data['payload']['headers'] if h['name'] == 'Subject'), '')

        label = classify_email(subject, snippet)
        label_counts[label] = label_counts.get(label, 0) + 1

        if label in ['Work', 'Updates', 'Other']:
            action_prompt = f"""This is an email:
Subject: {subject}
Body: {snippet}

Does this message contain a concrete action the user should take? Respond with the exact action in one sentence, or respond "None" if no action is needed."""

            result = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": action_prompt}]
            )

            action = result.choices[0].message.content.strip()
            if action and action.lower() != "none":
                action_items.append(f"{action} from '{subject}'")

    return {
        "total": len(message_ids),
        "breakdown": label_counts,
        "action_items": action_items[:5],
        "timestamp": datetime.utcnow().isoformat()
    }
