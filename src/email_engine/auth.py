import os
import os.path
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service(token_path=None):
    """
    Authenticate and return a Gmail API service object.
    Used for local development / CLI usage.

    Args:
        token_path: Path to the token JSON file. Defaults to TOKEN_FILE
                    env var, or 'token.json' in the current directory.
    """
    if token_path is None:
        token_path = os.environ.get('TOKEN_FILE', 'token.json')

    # Resolve credentials.json path (Render mounts secrets at /etc/secrets/)
    if os.environ.get("RENDER") == "true":
        creds_path = "/etc/secrets/credentials.json"
    else:
        creds_path = "credentials.json"

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
                creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    # Build and return the service object to interact with the API
    service = build('gmail', 'v1', credentials=creds)
    return service


def get_gmail_service_from_credentials(creds):
    """
    Build a Gmail service from pre-existing Credentials object.
    Used by the web OAuth flow in bridge.py.

    Args:
        creds: A google.oauth2.credentials.Credentials object.

    Returns:
        A Gmail API service object.
    """
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build('gmail', 'v1', credentials=creds)
    return service


def get_gmail_service_from_token_json(token_json_str, scopes=None):
    """
    Build a Gmail service from a token JSON string.
    Used for session-based authentication.

    Args:
        token_json_str: JSON string containing OAuth credentials.
        scopes: List of scopes. Defaults to SCOPES.

    Returns:
        Tuple of (Gmail API service, updated Credentials object).
    """
    if scopes is None:
        scopes = SCOPES

    token_data = json.loads(token_json_str)
    creds = Credentials.from_authorized_user_info(token_data, scopes)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build('gmail', 'v1', credentials=creds)
    return service, creds
