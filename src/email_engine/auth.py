import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service(token_path=None):
    """
    Authenticate and return a Gmail API service object.

    Args:
        token_path: Path to the token JSON file. Defaults to TOKEN_FILE
                    env var, or 'token.json' in the current directory.
    """
    if token_path is None:
        token_path = os.environ.get('TOKEN_FILE', 'token.json')

    creds = None
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This will trigger the browser-based authentication flow.
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    # Build and return the service object to interact with the API
    service = build('gmail', 'v1', credentials=creds)
    return service
