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
# Global state
# --------------------------------------------------
engine = None
my_km = None
peer_km = None
initialized = False

ROLE = sys.argv[1] if len(sys.argv) > 1 else "alice"

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
    global engine, my_km, peer_km, initialized

    if initialized:
        return jsonify({
            "status": "already_initialized",
            "role": ROLE
        })

    try:
        log.info(f"🔐 Initializing mTLS + QKD engine for role: {ROLE}")

        # --------------------------------------------------
        # Gmail OAuth → ONLY Alice
        # --------------------------------------------------
        # gmail_service = None
        # if ROLE == "alice":
        #     gmail_service = get_gmail_service()

        gmail_service = get_gmail_service()

        # --------------------------------------------------
        # QKD paths
        # --------------------------------------------------
        base_setup = os.path.join(os.getcwd(), "src", "Qukaydee_setup")
        ca_path = os.path.join(
            base_setup,
            "certs",
            "account-3000-server-ca-qukaydee-com.crt"
        )

        my_id = "sae-1" if ROLE == "alice" else "sae-2"
        peer_id = "sae-2" if ROLE == "alice" else "sae-1"
        role_dir = "alice_sender" if ROLE == "alice" else "bob_receiver"

        kme_url = (
            "https://kme-1.acct-3000.etsi-qkd-api.qukaydee.com"
            if ROLE == "alice"
            else "https://kme-2.acct-3000.etsi-qkd-api.qukaydee.com"
        )

        provider = QuKayDeeProvider(
            host=kme_url,
            cert_path=os.path.join(base_setup, role_dir, f"{my_id}.crt"),
            key_path=os.path.join(base_setup, role_dir, f"{my_id}.key"),
            ca_path=ca_path
        )

        my_km = KeyManager(
            my_id,
            qkd_provider=provider,
            storage_path=f"./key_store/{ROLE}"
        )

        # Peer KM stub (no QKD provider on purpose)
        peer_km = KeyManager(
            peer_id,
            storage_path=f"./key_store/{ROLE}_stub"
        )

        engine = QuantumEmailEngine(
            gmail_service,
            my_km,
            EncryptionEngine()
        )

        initialized = True
        log.info("✅ Backend initialization complete")

        return jsonify({
            "status": "success",
            "role": ROLE
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

    # Bob NEVER touches Gmail
    # if ROLE == "bob":
    #     return jsonify({
    #         "status": "success",
    #         "emails": []
    #     })

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
                id=m['id']
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
                "security_level": security_level
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
# SEND EMAIL (Alice only)
# --------------------------------------------------
@app.route('/api/send', methods=['POST'])
def send_mail():
    if not initialized:
        return require_initialized()

    if ROLE != "alice":
        return jsonify({
            "status": "error",
            "error": "Only Alice can send emails"
        }), 403

    data = request.json
    if not data or not all(k in data for k in ("recipient", "subject", "body", "security")):
        return jsonify({
            "status": "error",
            "error": "Invalid request payload"
        }), 400

    sec_map = {
        "standard": SecurityLevel.LEVEL_2_STANDARD,
        "confidential": SecurityLevel.LEVEL_3_HIGH,
        "top-secret": SecurityLevel.LEVEL_1_BASIC
    }

    try:
        result = engine.send_encrypted_email(
            sender="me",
            recipient=data['recipient'],
            subject=data['subject'],
            plaintext_content=data['body'],
            security_level=sec_map[data['security']],
            recipient_key_manager=peer_km
        )

        return jsonify(result)

    except Exception:
        log.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "error": "Failed to send email"
        }), 500


# --------------------------------------------------
# DECRYPT EMAIL (Bob only)
# --------------------------------------------------
@app.route('/api/decrypt', methods=['POST'])
def decrypt_mail():
    if not initialized:
        return require_initialized()

    if ROLE != "bob":
        return jsonify({
            "status": "error",
            "error": "Only Bob can decrypt emails"
        }), 403

    data = request.json
    if not data or "messageId" not in data:
        return jsonify({
            "status": "error",
            "error": "Missing messageId"
        }), 400

    try:
        result = engine.receive_encrypted_email(
            message_id=data['messageId'],
            receiver_key_manager=my_km
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
    port = 5000 if ROLE == "alice" else 5001
    app.run(port=port)