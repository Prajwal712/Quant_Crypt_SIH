import os
import sys
import json
import uuid
import logging
import traceback
from datetime import datetime, timezone

from flask import Flask, request, jsonify, redirect, session
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

# --------------------------------------------------
# Path setup
# --------------------------------------------------
sys.path.append(os.getcwd())

from src.email_engine.quantum_email import QuantumEmailEngine
from src.key_management.key_manager import KeyManager
from src.cryptography.security_levels import EncryptionEngine, SecurityLevel
from src.qkd.qukaydee_provider import QuKayDeeProvider

# --------------------------------------------------
# App + Logging
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("MailQ-Bridge")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "qmail-dev-secret-change-in-production")

# --------------------------------------------------
# CORS — allow Authorization header from frontend
# --------------------------------------------------
FRONTEND_ORIGIN = os.environ.get(
    "FRONTEND_ORIGIN",
    "https://quant-crypt-sih.vercel.app"
)

CORS(app, origins=[
    FRONTEND_ORIGIN,
    "http://localhost:5000",
    "http://localhost:8080",
    "http://127.0.0.1:5000",
    "http://127.0.0.1:8080",
], allow_headers=["Content-Type", "Authorization"])

# Render sets RENDER=true automatically on their servers
IS_RENDER = os.environ.get("RENDER") == "true"
PORT = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 5000))

# --------------------------------------------------
# Google OAuth Config
# --------------------------------------------------
SCOPES = ['https://www.googleapis.com/auth/gmail.modify',
          'https://www.googleapis.com/auth/userinfo.profile',
          'https://www.googleapis.com/auth/userinfo.email',
          'openid']

def _get_creds_path():
    """Resolve credentials.json path."""
    if IS_RENDER:
        return "/etc/secrets/credentials.json"
    return "credentials.json"


def _get_oauth_redirect_uri():
    """Get the OAuth callback URI based on environment."""
    if IS_RENDER:
        return os.environ.get(
            "OAUTH_REDIRECT_URI",
            "https://quantum-mail-api.onrender.com/api/auth/callback"
        )
    return "http://localhost:5000/api/auth/callback"


def _load_client_config():
    """
    Load OAuth client config. Supports both 'installed' and 'web' type
    credentials.json. Converts 'installed' type to 'web' type for the
    server-side OAuth flow.
    """
    creds_path = _get_creds_path()
    with open(creds_path, 'r') as f:
        data = json.load(f)

    redirect_uri = _get_oauth_redirect_uri()

    # If it's an "installed" type, convert to "web" type for server flow
    if "installed" in data:
        installed = data["installed"]
        return {
            "web": {
                "client_id": installed["client_id"],
                "project_id": installed.get("project_id", ""),
                "auth_uri": installed["auth_uri"],
                "token_uri": installed["token_uri"],
                "auth_provider_x509_cert_url": installed.get("auth_provider_x509_cert_url", ""),
                "client_secret": installed["client_secret"],
                "redirect_uris": [redirect_uri],
            }
        }
    # Already a "web" type
    if "web" in data:
        data["web"]["redirect_uris"] = [redirect_uri]
        return data

    raise ValueError("credentials.json must contain 'installed' or 'web' key")


# --------------------------------------------------
# Per-user session store (in-memory)
# For production, use Redis or a database
# --------------------------------------------------
user_sessions = {}  # session_id -> { creds_json, user_info, engine, decrypted_cache, ... }


def _get_session_id():
    """
    Get session ID from the Authorization: Bearer <token> header.
    Falls back to Flask session cookie for local dev.
    """
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    # Fallback: Flask session cookie (works for same-domain / local dev)
    return session.get("sid")


def _get_user_session():
    """Get the user session dict, or None if not logged in."""
    sid = _get_session_id()
    if not sid or sid not in user_sessions:
        return None
    return user_sessions[sid]


def _build_gmail_service_from_creds(creds_json):
    """Build a Gmail service from stored credentials JSON."""
    creds = Credentials.from_authorized_user_info(json.loads(creds_json), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build('gmail', 'v1', credentials=creds), creds


def _get_user_info(creds):
    """Fetch user profile info from Google."""
    service = build('oauth2', 'v2', credentials=creds)
    user_info = service.userinfo().get().execute()
    return user_info


# --------------------------------------------------
# SAE helpers (shared across all users)
# --------------------------------------------------
def _cert_path(filename):
    """
    Resolve a certificate file path.
    On Render: /etc/secrets/<filename>   (flat mount)
    Locally:   returned as-is            (nested directory)
    """
    if IS_RENDER:
        flat_name = os.path.basename(filename)
        return f"/etc/secrets/{flat_name}"
    return filename


def _init_qkd_managers():
    """Initialize QKD key managers (shared across all users)."""
    base_setup = os.path.join(os.getcwd(), "src", "Qukaydee_setup")
    ca_file = os.path.join(base_setup, "certs", "account-3000-server-ca-qukaydee-com.crt")

    # SAE-1 → for ENCRYPTION
    send_provider = QuKayDeeProvider(
        host="https://kme-1.acct-3000.etsi-qkd-api.qukaydee.com",
        cert_path=_cert_path(os.path.join(base_setup, "alice_sender", "sae-1.crt")),
        key_path=_cert_path(os.path.join(base_setup, "alice_sender", "sae-1.key")),
        ca_path=_cert_path(ca_file)
    )
    send_km = KeyManager("sae-1", qkd_provider=send_provider, storage_path="./key_store/sae-1")

    # SAE-2 → for DECRYPTION
    decrypt_provider = QuKayDeeProvider(
        host="https://kme-2.acct-3000.etsi-qkd-api.qukaydee.com",
        cert_path=_cert_path(os.path.join(base_setup, "bob_receiver", "sae-2.crt")),
        key_path=_cert_path(os.path.join(base_setup, "bob_receiver", "sae-2.key")),
        ca_path=_cert_path(ca_file)
    )
    decrypt_km = KeyManager("sae-2", qkd_provider=decrypt_provider, storage_path="./key_store/sae-2")

    return send_km, decrypt_km


# Initialize QKD managers once at startup (shared resource)
send_key_manager = None
decrypt_key_manager = None
qkd_initialized = False


def _ensure_qkd():
    """Lazy-init QKD managers."""
    global send_key_manager, decrypt_key_manager, qkd_initialized
    if not qkd_initialized:
        send_key_manager, decrypt_key_manager = _init_qkd_managers()
        qkd_initialized = True
        log.info("✅ QKD managers initialized (sae-1 encrypt, sae-2 decrypt)")


# --------------------------------------------------
# AUTH ENDPOINTS
# --------------------------------------------------
@app.route('/api/auth/google', methods=['GET'])
def auth_google():
    """
    Start Google OAuth flow.
    Browser navigates directly here (top-level navigation, NOT fetch).
    This is critical: top-level navigation makes the browser treat
    Render as a first-party context, so cookies survive.
    """
    try:
        client_config = _load_client_config()
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=_get_oauth_redirect_uri()
        )

        # 1. Generate the standard auth URL and state
        auth_url, original_state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )

        # 2. Append the code_verifier to the state string
        #    This bypasses the need for cross-domain session cookies
        #    between the /auth/google and /auth/callback requests
        passthrough_state = f"{original_state}---{flow.code_verifier}"

        # 3. Regenerate the URL with the new combined state string
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=passthrough_state
        )

        # Direct redirect (NOT a JSON response) — this is a top-level
        # navigation so the browser treats us as first-party
        return redirect(auth_url)

    except Exception:
        log.error(traceback.format_exc())
        return redirect(f"{FRONTEND_ORIGIN}?auth=error")


@app.route('/api/auth/callback', methods=['GET'])
def auth_callback():
    """
    Google OAuth callback.
    Exchanges authorization code for tokens, creates user session,
    and redirects back to frontend.
    """
    try:
        code = request.args.get('code')
        if not code:
            return jsonify({"status": "error", "error": "No authorization code"}), 400

        # 1. Grab the combined state parameter from the incoming Google redirect
        incoming_state = request.args.get('state', '')

        # 2. Extract the code_verifier back out of the state string
        if "---" in incoming_state:
            original_state, code_verifier = incoming_state.split("---", 1)
        else:
            log.error("Invalid state parameter: missing code verifier delimiter.")
            return redirect(f"{FRONTEND_ORIGIN}?auth=error")

        client_config = _load_client_config()
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            state=incoming_state,  # Must pass the exact combined string back to the flow
            redirect_uri=_get_oauth_redirect_uri()
        )

        # 3. Exchange code for tokens using the extracted verifier
        flow.fetch_token(code=code, code_verifier=code_verifier)
        creds = flow.credentials

        # Get user info
        user_info = _get_user_info(creds)

        # Create a session token (this is sent to the frontend via URL,
        # NOT via a cookie — completely avoids cross-domain cookie issues)
        sid = str(uuid.uuid4())

        user_sessions[sid] = {
            'creds_json': creds.to_json(),
            'user_info': {
                'name': user_info.get('name', 'User'),
                'email': user_info.get('email', ''),
                'picture': user_info.get('picture', ''),
            },
            'decrypted_cache': {},  # message_id -> decrypted content
        }

        log.info(f"✅ User signed in: {user_info.get('email')}")

        # Redirect to frontend with session token in the URL.
        # The frontend stores this in sessionStorage and sends it
        # as Authorization: Bearer <token> on every API call.
        return redirect(f"{FRONTEND_ORIGIN}?auth=success&token={sid}")

    except Exception:
        log.error(traceback.format_exc())
        return redirect(f"{FRONTEND_ORIGIN}?auth=error")


# --------------------------------------------------
# USER INFO
# --------------------------------------------------
@app.route('/api/me', methods=['GET'])
def get_me():
    """Return the current user's info if logged in."""
    user_session = _get_user_session()
    if not user_session:
        return jsonify({"status": "not_authenticated"}), 401

    return jsonify({
        "status": "success",
        "user": user_session['user_info']
    })


# --------------------------------------------------
# INIT (now per-user, auto-initializes QKD on first call)
# --------------------------------------------------
@app.route('/api/init', methods=['POST'])
def initialize():
    """
    Initialize the QKD engine for the currently signed-in user.
    Requires the user to be authenticated via OAuth first.
    """
    user_session = _get_user_session()
    if not user_session:
        return jsonify({
            "status": "error",
            "error": "Not authenticated. Please sign in with Google first."
        }), 401

    try:
        _ensure_qkd()

        # Build Gmail service from user's OAuth token
        gmail_service, updated_creds = _build_gmail_service_from_creds(
            user_session['creds_json']
        )

        # Update stored credentials (they might have been refreshed)
        user_session['creds_json'] = updated_creds.to_json()

        # Create per-user engine
        engine = QuantumEmailEngine(
            gmail_service,
            send_key_manager,
            EncryptionEngine()
        )

        user_session['engine'] = engine
        user_session['gmail_service'] = gmail_service

        log.info(f"✅ Engine initialized for {user_session['user_info']['email']}")

        return jsonify({
            "status": "success",
            "identity": "sae-1 (encrypt) / sae-2 (decrypt)",
            "user": user_session['user_info']
        })

    except Exception:
        log.error("❌ Initialization failed")
        log.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": "Initialization failed. Check server logs."
        }), 500


# --------------------------------------------------
# LIST EMAILS (all recent + quantum-encrypted)
# --------------------------------------------------
@app.route('/api/list', methods=['GET'])
def list_messages():
    user_session = _get_user_session()
    if not user_session or 'engine' not in user_session:
        return jsonify({
            "status": "error",
            "error": "Not initialized. Call /api/init first."
        }), 400

    try:
        gmail_service = user_session['gmail_service']
        filter_type = request.args.get('filter', 'quantum')  # 'quantum' or 'all'

        if filter_type == 'all':
            # Fetch ALL recent emails
            results = gmail_service.users().messages().list(
                userId='me',
                maxResults=20
            ).execute()
        else:
            # Fetch only quantum-encrypted emails
            results = gmail_service.users().messages().list(
                userId='me',
                q='[QUANTUM-ENCRYPTED]',
                maxResults=10
            ).execute()

        messages = results.get('messages', [])
        emails = []

        for m in messages:
            msg = gmail_service.users().messages().get(
                userId='me',
                id=m['id'],
                format='metadata',
                metadataHeaders=['Subject', 'From', 'Date', 'X-Quantum-Security']
            ).execute()

            headers = msg['payload'].get('headers', [])
            raw_subject = next(
                (h['value'] for h in headers if h['name'].lower() == 'subject'),
                None
            )

            is_quantum = False
            if raw_subject and "[QUANTUM-ENCRYPTED]" in raw_subject:
                subject = raw_subject.replace("[QUANTUM-ENCRYPTED]", "").strip()
                is_quantum = True
            elif raw_subject:
                subject = raw_subject
            else:
                subject = "(No subject)"

            sender = next(
                (h['value'] for h in headers if h['name'] == 'From'),
                "Unknown"
            )

            date_str = next(
                (h['value'] for h in headers if h['name'] == 'Date'),
                "Unknown"
            )

            security_level = int(next(
                (h['value'] for h in headers if h['name'] == 'X-Quantum-Security'),
                "2"  # default AES-GCM
            )) if is_quantum else 0

            # Check if this email was already decrypted in this session
            is_cached = m['id'] in user_session.get('decrypted_cache', {})

            emails.append({
                "id": m['id'],
                "sender": sender,
                "subject": subject,
                "time": date_str,
                "read": is_cached,
                "folder": "inbox",
                "security_level": security_level,
                "is_quantum": is_quantum,
                "is_decrypted": is_cached,
            })

        return jsonify({
            "status": "success",
            "emails": emails
        })

    except Exception:
        log.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": "Failed to list emails"
        }), 500


# --------------------------------------------------
# SEND ENCRYPTED EMAIL
# --------------------------------------------------
@app.route('/api/send', methods=['POST'])
def send_mail():
    user_session = _get_user_session()
    if not user_session or 'engine' not in user_session:
        return jsonify({
            "status": "error",
            "error": "Not initialized. Call /api/init first."
        }), 400

    data = request.json
    if not data or not all(k in data for k in ("recipient", "subject", "body", "security")):
        return jsonify({
            "status": "error",
            "error": "Invalid request payload"
        }), 400

    try:
        engine = user_session['engine']

        # enc_keys → SAE-1 encrypts, peer is sae-2
        result = engine.send_encrypted_email(
            sender="me",
            recipient=data['recipient'],
            subject=data['subject'],
            plaintext_content=data['body'],
            security_level=SecurityLevel(int(data["security"])),
            recipient_key_manager=KeyManager(
                "sae-2",
                storage_path="./key_store/sae-1_peer_stub"
            )
        )

        return jsonify(result)

    except Exception:
        log.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": "Failed to send email"
        }), 500


# --------------------------------------------------
# DECRYPT RECEIVED EMAIL
# --------------------------------------------------
@app.route('/api/decrypt', methods=['POST'])
def decrypt_mail():
    user_session = _get_user_session()
    if not user_session or 'engine' not in user_session:
        return jsonify({
            "status": "error",
            "error": "Not initialized. Call /api/init first."
        }), 400

    data = request.json
    if not data or "messageId" not in data:
        return jsonify({
            "status": "error",
            "error": "Missing messageId"
        }), 400

    message_id = data['messageId']

    # Check if already decrypted in this session (return cached)
    decrypted_cache = user_session.get('decrypted_cache', {})
    if message_id in decrypted_cache:
        log.info(f"📦 Returning cached decrypted email: {message_id}")
        return jsonify(decrypted_cache[message_id])

    try:
        engine = user_session['engine']

        # dec_keys → SAE-2 retrieves key that SAE-1 used to encrypt
        result = engine.receive_encrypted_email(
            message_id=message_id,
            receiver_key_manager=decrypt_key_manager
        )

        # Cache the decrypted result in the user's session
        if result.get("status") == "success":
            user_session['decrypted_cache'][message_id] = result
            log.info(f"🔓 Decrypted and cached email: {message_id}")

        return jsonify(result)

    except Exception:
        log.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": "Decryption failed"
        }), 500


# --------------------------------------------------
# GET CACHED DECRYPTED EMAILS
# --------------------------------------------------
@app.route('/api/decrypted-cache', methods=['GET'])
def get_decrypted_cache():
    """Return all decrypted emails from this session."""
    user_session = _get_user_session()
    if not user_session:
        return jsonify({"status": "error", "error": "Not authenticated"}), 401

    cache = user_session.get('decrypted_cache', {})
    return jsonify({
        "status": "success",
        "decrypted_emails": cache
    })


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------
@app.route("/api/logout", methods=["POST"])
def logout():
    try:
        sid = _get_session_id()
        if sid and sid in user_sessions:
            email = user_sessions[sid].get('user_info', {}).get('email', 'unknown')
            del user_sessions[sid]
            log.info(f"👋 User signed out: {email}")

        return jsonify({"status": "success"})
    except Exception:
        log.error(traceback.format_exc())
        return jsonify({"status": "error"}), 500


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "qkd_initialized": qkd_initialized,
        "active_sessions": len(user_sessions)
    })


# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == '__main__':
    # Allow OAuth over HTTP for local development
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    print(f"\n🚀 Starting MailQ Bridge on port {PORT}")
    print(f"   Encrypt: SAE-1 (kme-1) → enc_keys")
    print(f"   Decrypt: SAE-2 (kme-2) → dec_keys")
    print(f"   OAuth callback: {_get_oauth_redirect_uri()}\n")
    app.run(port=PORT, debug=True)