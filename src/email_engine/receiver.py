# receiver.py
import base64
from .auth import get_gmail_service

def get_latest_email(service, user_id='me'):
    try:
    
        results = service.users().messages().list(userId=user_id, q="is:unread", maxResults=1).execute()
        messages = results.get('messages', [])

        if not messages:
            print("No new unread messages found.")
            return

        # Get the full message details for the latest message
        msg = service.users().messages().get(userId=user_id, id=messages[0]['id']).execute()
        
        # The actual email content is in the payload
        payload = msg['payload']
        headers = payload['headers']

        # Extract Subject and Sender
        subject = next(header['value'] for header in headers if header['name'] == 'Subject')
        sender = next(header['value'] for header in headers if header['name'] == 'From')

        print(f"From: {sender}")
        print(f"Subject: {subject}")
        print("-" * 20)

        # The body of the email can be in parts (e.g., plain text and HTML)
        if 'parts' in payload:
            part = payload['parts'][0]
            data = part['body']['data']
        else:
            data = payload['body']['data']
            
        # The data is base64 encoded, so we need to decode it
        decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
        print(decoded_data)

    except Exception as e:
        print(f'An error occurred: {e}')

if __name__ == '__main__':
    service = get_gmail_service()
    print("Checking for the latest unread email...")
    get_latest_email(service)