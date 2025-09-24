import base64
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError

def create_message(sender, to, subject, message_text):
   
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject  
    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': raw_message}

def send_email(service, user_id, message):
    
    try:
        sent_message = service.users().messages().send(userId=user_id, body=message).execute()
        print(f"Message sent successfully. Message ID: {sent_message['id']}")
        return sent_message
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None
