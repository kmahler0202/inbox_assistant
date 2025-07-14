from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_action_items(subject, body):
    prompt = f"""
You are a professional assistant. Your job is to extract actionable items from emails. Only extract tasks where the user needs to take direct action such as replying, attending, confirming, submitting, or following up.

RULES:
- Focus on action items that require personal effort.
- Do not include advertisements, promotions, or marketing calls-to-action.
- If no action is required, respond "None".
- If multiple actions are required, list them each on a new line.

Subject: {subject}

Body: {body}

List the action items below:
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a professional assistant who extracts action items."},
            {"role": "user", "content": prompt}
        ]
    )

    action_items = response.choices[0].message.content.strip()
    
    # Return a list, splitting by lines and removing empty strings
    action_list = [item.strip() for item in action_items.split('\n') if item.strip() and item.lower() != "none"]
    return action_list
