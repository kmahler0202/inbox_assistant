from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes required for Gmail push + reading messages
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']

def main():
    # Load credentials or go through OAuth flow
    creds = None
    try:
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    except:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    request = {
        'labelIds': ['INBOX'],
        'topicName': 'projects/YOUR_PROJECT_ID/topics/YOUR_TOPIC_NAME'
    }

    response = service.users().watch(userId='me', body=request).execute()
    print("Watch started successfully:")
    print(response)

if __name__ == '__main__':
    main()
