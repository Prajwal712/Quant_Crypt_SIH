import os
import sys
import logging
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS

# Ensure internal module pathing works from root
sys.path.append(os.getcwd())

from src.email_engine.auth import get_gmail_service
from src.email_engine.quantum_email import QuantumEmailEngine
from src.key_management.key_manager import KeyManager
from src.cryptography.security_levels import EncryptionEngine, SecurityLevel
from src.qkd.qukaydee_provider import QuKayDeeProvider

# Setup Logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("MailQ-Bridge")

app = Flask(__name__)
CORS(app)

# Global instances
engine = None
my_km = None
peer_km = None
ROLE = sys.argv[1] if len(sys.argv) > 1 else "alice"

@app.route('/api/init', methods=['POST'])
def initialize():
    global engine, my_km, peer_km
    try:
        log.info(f"Initializing mTLS tunnel for role: {ROLE}")
        service = get_gmail_service()
        
        # Resolve paths for QuKayDee setup
        base_setup = os.path.join(os.getcwd(), "src", "Qukaydee_setup")
        ca_path = os.path.join(base_setup, "certs", "account-3000-server-ca-qukaydee-com.crt")
        
        # Configure Provider based on ROLE
        my_id = "sae-1" if ROLE == "alice" else "sae-2"
        peer_id = "sae-2" if ROLE == "alice" else "sae-1"
        role_dir = "alice_sender" if ROLE == "alice" else "bob_receiver"
        
        kme_url = f"https://kme-{'1' if ROLE == 'alice' else '2'}.acct-3000.etsi-qkd-api.qukaydee.com"

        provider = QuKayDeeProvider(
            host=kme_url,
            cert_path=os.path.join(base_setup, role_dir, f"{my_id}.crt"),
            key_path=os.path.join(base_setup, role_dir, f"{my_id}.key"),
            ca_path=ca_path
        )

        my_km = KeyManager(my_id, qkd_provider=provider, storage_path=f"./key_store/{ROLE}")
        peer_km = KeyManager(peer_id, storage_path=f"./key_store/{ROLE}_stub")
        engine = QuantumEmailEngine(service, my_km, EncryptionEngine())
        
        return jsonify({"status": "success", "role": ROLE})
    except Exception as e:
        log.error(f"Initialization Failed: {traceback.format_exc()}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/list', methods=['GET'])
def list_messages():
    """Fetch unread emails for the UI"""
    try:
        results = engine.gmail_service.users().messages().list(userId='me', q="is:unread", maxResults=5).execute()
        messages = results.get('messages', [])
        
        emails = []
        for m in messages:
            msg = engine.gmail_service.users().messages().get(userId='me', id=m['id']).execute()
            headers = msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
            emails.append({"id": m['id'], "sender": sender, "subject": subject, "time": "Just now", "read": False, "folder": "inbox"})
        return jsonify({"status": "success", "emails": emails})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/send', methods=['POST'])
def send_mail():
    data = request.json
    sec_map = {"standard": SecurityLevel.LEVEL_2_STANDARD, "confidential": SecurityLevel.LEVEL_3_HIGH, "top-secret": SecurityLevel.LEVEL_1_BASIC}
    result = engine.send_encrypted_email(
        sender="me", recipient=data['recipient'], subject=data['subject'],
        plaintext_content=data['body'], security_level=sec_map[data['security']],
        recipient_key_manager=peer_km
    )
    return jsonify(result)

@app.route('/api/decrypt', methods=['POST'])
def decrypt_mail():
    data = request.json
    result = engine.receive_encrypted_email(message_id=data['messageId'], receiver_key_manager=my_km)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=5000)