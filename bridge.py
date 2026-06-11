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
CORS(app, origins=["https://quant-crypt-sih.vercel.app", "http://localhost:5000"])

# --------------------------------------------------
# SAE Configuration
# --------------------------------------------------
# Architecture:
#   SAE-1 (kme-1, alice_sender certs) → used for ENCRYPTION on both machines
#   SAE-2 (kme-2, bob_receiver certs) → used for DECRYPTION on both machines
#
# Usage:
#   python3 bridge.py              → runs on port 5000 (default)
#   python3 bridge.py <port>       → runs on specified port
# --------------------------------------------------

PORT = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 5000))
TOKEN_FILE = os.environ.get("TOKEN_FILE", f"token_{PORT}.json")


# --------------------------------------------------
# Global state
# --------------------------------------------------
engine = None
send_key_manager = None     # SAE-1 for encryption
decrypt_key_manager = None  # SAE-2 for decryption
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
    global engine, send_key_manager, decrypt_key_manager, initialized

    if initialized:
        return jsonify({
            "status": "already_initialized",
            "identity": "sae-1 (encrypt) / sae-2 (decrypt)"
        })

    try:
        log.info("🔐 Initializing dual-SAE QKD engine (sae-1→encrypt, sae-2→decrypt)")

        # --------------------------------------------------
        # Gmail OAuth
        # --------------------------------------------------
        gmail_service = get_gmail_service(token_path=TOKEN_FILE)

        # --------------------------------------------------
        # Paths
        # --------------------------------------------------
        base_setup = os.path.join(os.getcwd(), "src", "Qukaydee_setup")
        ca_path = os.path.join(
            base_setup,
            "certs",
            "account-3000-server-ca-qukaydee-com.crt"
        )

        # --------------------------------------------------
        # SAE-1 provider → for ENCRYPTION (enc_keys via kme-1)
        # --------------------------------------------------
        send_provider = QuKayDeeProvider(
            host="https://kme-1.acct-3000.etsi-qkd-api.qukaydee.com",
            cert_path=os.path.join(base_setup, "alice_sender", "sae-1.crt"),
            key_path=os.path.join(base_setup, "alice_sender", "sae-1.key"),
            ca_path=ca_path
        )

        send_key_manager = KeyManager(
            "sae-1",
            qkd_provider=send_provider,
            storage_path="./key_store/sae-1"
        )

        # --------------------------------------------------
        # SAE-2 provider → for DECRYPTION (dec_keys via kme-2)
        # --------------------------------------------------
        decrypt_provider = QuKayDeeProvider(
            host="https://kme-2.acct-3000.etsi-qkd-api.qukaydee.com",
            cert_path=os.path.join(base_setup, "bob_receiver", "sae-2.crt"),
            key_path=os.path.join(base_setup, "bob_receiver", "sae-2.key"),
            ca_path=ca_path
        )

        decrypt_key_manager = KeyManager(
            "sae-2",
            qkd_provider=decrypt_provider,
            storage_path="./key_store/sae-2"
        )

        # --------------------------------------------------
        # Engine uses SAE-1 (send_key_manager) as the sender identity
        # --------------------------------------------------
        engine = QuantumEmailEngine(
            gmail_service,
            send_key_manager,
            EncryptionEngine()
        )

        initialized = True
        log.info(f"✅ Backend ready — sae-1 (encrypt) + sae-2 (decrypt) on port {PORT}")

        return jsonify({
            "status": "success",
            "identity": "sae-1 (encrypt) / sae-2 (decrypt)"
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
    if not initialized:
        return require_initialized()

    data = request.json
    if not data or "messageId" not in data:
        return jsonify({
            "status": "error",
            "error": "Missing messageId"
        }), 400

    try:
        # dec_keys → SAE-2 retrieves key that SAE-1 used to encrypt
        result = engine.receive_encrypted_email(
            message_id=data['messageId'],
            receiver_key_manager=decrypt_key_manager
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
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        return jsonify({"status": "success"})
    except Exception:
        return jsonify({"status": "error"}), 500


# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == '__main__':
    print(f"\n🚀 Starting MailQ Bridge on port {PORT}")
    print(f"   Encrypt: SAE-1 (kme-1) → enc_keys")
    print(f"   Decrypt: SAE-2 (kme-2) → dec_keys\n")
    app.run(port=PORT)