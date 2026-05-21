import os
import sys
import logging
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS

# --------------------------------------------------
# Path setup
# --------------------------------------------------
sys.path.append(os.getcwd())

from src.email_engine.auth import get_gmail_service
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
CORS(app)

# --------------------------------------------------
# SAE Configuration
# --------------------------------------------------
# Usage:
#   python3 bridge.py           → runs as sae-1 (port 5000)
#   python3 bridge.py sae-2     → runs as sae-2 (port 5001)
#
# Both instances can SEND and DECRYPT — no role guards.
# The argument only determines which SAE identity / KME / certs to use.
# --------------------------------------------------

SAE_CONFIG = {
    "sae-1": {
        "my_id":    "sae-1",
        "peer_id":  "sae-2",
        "kme_url":  "https://kme-1.acct-3000.etsi-qkd-api.qukaydee.com",
        "cert_dir": "alice_sender",
        "port":     5000,
    },
    "sae-2": {
        "my_id":    "sae-2",
        "peer_id":  "sae-1",
        "kme_url":  "https://kme-2.acct-3000.etsi-qkd-api.qukaydee.com",
        "cert_dir": "bob_receiver",
        "port":     5001,
    },
}

# Pick identity from CLI arg (default: sae-1)
IDENTITY = sys.argv[1] if len(sys.argv) > 1 else "sae-1"
if IDENTITY not in SAE_CONFIG:
    print(f"❌ Unknown identity '{IDENTITY}'. Use: sae-1 or sae-2")
    sys.exit(1)

CFG = SAE_CONFIG[IDENTITY]

# --------------------------------------------------
# Global state
# --------------------------------------------------
engine = None
key_manager = None
initialized = False


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def require_initialized():
    return jsonify({
        "status": "error",
        "error": "Backend not initialized. Call /api/init first."
    }), 400


# --------------------------------------------------
# INIT
# --------------------------------------------------
@app.route('/api/init', methods=['POST'])
def initialize():
    global engine, key_manager, initialized

    if initialized:
        return jsonify({
            "status": "already_initialized",
            "identity": CFG["my_id"]
        })

    try:
        log.info(f"🔐 Initializing QKD engine as {CFG['my_id']} (peer: {CFG['peer_id']})")

        # --------------------------------------------------
        # Gmail OAuth
        # --------------------------------------------------
        gmail_service = get_gmail_service()

        # --------------------------------------------------
        # QKD provider — uses this identity's certs + KME
        # enc_keys (send) and dec_keys (decrypt) both go
        # through the same KME with the same certs.
        # --------------------------------------------------
        base_setup = os.path.join(os.getcwd(), "src", "Qukaydee_setup")
        ca_path = os.path.join(
            base_setup,
            "certs",
            "account-3000-server-ca-qukaydee-com.crt"
        )

        provider = QuKayDeeProvider(
            host=CFG["kme_url"],
            cert_path=os.path.join(base_setup, CFG["cert_dir"], f"{CFG['my_id']}.crt"),
            key_path=os.path.join(base_setup, CFG["cert_dir"], f"{CFG['my_id']}.key"),
            ca_path=ca_path
        )

        # --------------------------------------------------
        # Single KeyManager — both send + decrypt
        # --------------------------------------------------
        key_manager = KeyManager(
            CFG["my_id"],
            qkd_provider=provider,
            storage_path=f"./key_store/{CFG['my_id']}"
        )

        engine = QuantumEmailEngine(
            gmail_service,
            key_manager,
            EncryptionEngine()
        )

        initialized = True
        log.info(f"✅ Backend ready — {CFG['my_id']} on port {CFG['port']}")

        return jsonify({
            "status": "success",
            "identity": CFG["my_id"]
        })

    except Exception:
        log.error("❌ Initialization failed")
        log.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": "Initialization failed. Check server logs."
        }), 500


# --------------------------------------------------
# LIST EMAILS
# --------------------------------------------------
@app.route('/api/list', methods=['GET'])
def list_messages():
    if not initialized:
        return require_initialized()

    try:
        results = engine.gmail_service.users().messages().list(
            userId='me',
            q='[QUANTUM-ENCRYPTED]',
            maxResults=10
        ).execute()

        messages = results.get('messages', [])
        emails = []

        for m in messages:
            msg = engine.gmail_service.users().messages().get(
                userId='me',
                id=m['id'],
                format='metadata',
                metadataHeaders=['Subject', 'From', 'X-Quantum-Security']
            ).execute()

            headers = msg['payload'].get('headers', [])
            raw_subject = next(
                (h['value'] for h in headers if h['name'].lower() == 'subject'),
                None
            )

            if raw_subject:
                subject = raw_subject.replace("[QUANTUM-ENCRYPTED]", "").strip()
            else:
                subject = "(No subject)"
            sender = next(
                (h['value'] for h in headers if h['name'] == 'From'),
                "Unknown"
            )
            security_level = int(next(
                (h['value'] for h in headers if h['name'] == 'X-Quantum-Security'),
                "2"  # default AES-GCM
            ))

            emails.append({
                "id": m['id'],
                "sender": sender,
                "subject": subject,
                "time": "Just now",
                "read": False,
                "folder": "inbox",
                "security_level": security_level,
                "is_quantum": True
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
    if not initialized:
        return require_initialized()

    data = request.json
    if not data or not all(k in data for k in ("recipient", "subject", "body", "security")):
        return jsonify({
            "status": "error",
            "error": "Invalid request payload"
        }), 400

    try:
        # enc_keys → peer SAE
        result = engine.send_encrypted_email(
            sender="me",
            recipient=data['recipient'],
            subject=data['subject'],
            plaintext_content=data['body'],
            security_level=SecurityLevel(int(data["security"])),
            recipient_key_manager=KeyManager(
                CFG["peer_id"],
                storage_path=f"./key_store/{CFG['my_id']}_peer_stub"
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
    if not initialized:
        return require_initialized()

    data = request.json
    if not data or "messageId" not in data:
        return jsonify({
            "status": "error",
            "error": "Missing messageId"
        }), 400

    try:
        # dec_keys → retrieve key that peer used to encrypt
        result = engine.receive_encrypted_email(
            message_id=data['messageId'],
            receiver_key_manager=key_manager
        )
        return jsonify(result)

    except Exception:
        log.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": "Decryption failed"
        }), 500


@app.route("/api/logout", methods=["POST"])
def logout():
    try:
        token_path = "./token.json"
        if os.path.exists(token_path):
            os.remove(token_path)
        return jsonify({"status": "success"})
    except Exception:
        return jsonify({"status": "error"}), 500


# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == '__main__':
    print(f"\n🚀 Starting MailQ Bridge as {CFG['my_id']} on port {CFG['port']}")
    print(f"   Peer: {CFG['peer_id']}")
    print(f"   KME:  {CFG['kme_url']}\n")
    app.run(port=CFG["port"])