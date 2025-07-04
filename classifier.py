# CLASSIFIER FROM EMAIL ORGANIZER V3
# GPT-4.1-mini powered email label classifier using structured categories and system instructions.
# adapted to work with google aps inbox assistant v1

from openai import OpenAI
import os

# Limit email body length to reduce token usage
MAX_SNIPPET_LEN = 500

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def classify_email(subject, snippet):
    # Truncate long snippets for token efficiency
    snippet = snippet[:MAX_SNIPPET_LEN]

    # System prompt with label definitions
    prompt_system = """You are an AI email assistant. Your job is to classify emails into exactly one of the following categories:

        - Work: Related to your job, coworkers, meetings, projects, or career.
        - Personal: Friends, family, or one-on-one communication that is not work-related.
        - Promotions: Sales, discounts, offers, deals, or marketing campaigns.
        - Spam: Unwanted or irrelevant messages, scams, or low-quality bulk email.
        - Newsletter: Regular subscriptions from blogs, authors, or organizations.
        - Receipt: Order confirmations, payment receipts, shipping details.
        - Sportsbook: Gambling, betting, or fantasy sports content.
        - Subscriptions: Account updates, sign-up confirmations, or content access emails.
        - Social: Notifications from social media (e.g., likes, follows, comments).
        - Updates: Informational emails from apps or services (e.g., 'Your password was changed').
        - Forums: Messages from discussion boards or online communities.
        - Other: Anything that doesn't fit the categories above."""

    # Actual email content to classify
    user_prompt = f"Subject: {subject}\nBody: {snippet}\n\nRespond only with the category name."

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content.strip()
