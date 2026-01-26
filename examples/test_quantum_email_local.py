from src.key_management.key_manager import KeyManager
from src.cryptography.security_levels import (
    EncryptionEngine,
    SecurityLevel,
    generate_rsa_keypair,
)
from src.email_engine.quantum_email import QuantumEmailEngine
from src.qkd.local_provider import LocalQKDProvider
import base64

# ==========================================================
# Dummy Gmail Service (minimal, correct)
# ==========================================================

class DummyGmailService:
    def __init__(self):
        self.storage = {}

    class Users:
        def __init__(self, service):
            self.service = service

        class Messages:
            def __init__(self, service):
                self.service = service

            def send(self, userId, body):
                msg_id = f"msg-{len(self.service.storage) + 1}"
                self.service.storage[msg_id] = body

                class Resp:
                    def execute(self_inner):
                        return {"id": msg_id}

                return Resp()

            def get(self, userId, id):
                stored = self.service.storage[id]

                # 🔥 Decode full MIME first
                mime_bytes = base64.urlsafe_b64decode(stored["raw"])
                mime_text = mime_bytes.decode("utf-8")

                # 🔥 Extract body after blank line (RFC 5322)
                body = mime_text.split("\n\n", 1)[1]

                class Resp:
                    def execute(self_inner):
                        return {
                            "payload": {
                                "headers": [
                                    {"name": "Subject", "value": "Hello Quantum"},
                                    {"name": "From", "value": "alice@example.com"},
                                ],
                                "parts": [
                                    {
                                        "mimeType": "text/plain",
                                        "body": {
                                            # Gmail-style: base64(body only)
                                            "data": base64.urlsafe_b64encode(
                                                body.encode("utf-8")
                                            ).decode("utf-8")
                                        }
                                    }
                                ]
                            }
                        }

                return Resp()

        def messages(self):
            return DummyGmailService.Users.Messages(self.service)

    def users(self):
        return DummyGmailService.Users(self)


# ==========================================================
# End-to-End Local Test
# ==========================================================

def test_end_to_end():
    print("\n=== Quantum Email Local Test ===")

    # -------------------------
    # Core components
    # -------------------------

    # 🔑 LOCAL QKD provider (BB84 simulator)
    qkd_provider = LocalQKDProvider(key_length=256)

    crypto = EncryptionEngine()
    gmail = DummyGmailService()

    # -------------------------
    # Key Managers (IMPORTANT FIX)
    # -------------------------

    alice_km = KeyManager(
        manager_id="sae-1",
        qkd_provider=qkd_provider,
    )

    bob_km = KeyManager(
        manager_id="sae-2",
        qkd_provider=qkd_provider,
    )

    # -------------------------
    # Quantum Email Engine
    # -------------------------

    engine = QuantumEmailEngine(
        gmail_service=gmail,
        sender_key_manager=alice_km,
        encryption_engine=crypto,
    )

    # RSA keys (Level 4 readiness)
    private_key, public_key = generate_rsa_keypair()

    # -------------------------
    # SEND
    # -------------------------

    send_result = engine.send_encrypted_email(
        sender="alice@example.com",
        recipient="bob@example.com",
        subject="Hello Quantum",
        plaintext_content="Hello Bob, quantum world!",
        security_level=SecurityLevel.LEVEL_2_STANDARD,
        recipient_key_manager=bob_km,
        recipient_public_key=public_key,
    )

    print("SEND RESULT:", send_result)

    if send_result["status"] != "success":
        raise RuntimeError(f"Send failed: {send_result}")

    # -------------------------
    # RECEIVE
    # -------------------------

    recv_result = engine.receive_encrypted_email(
        message_id=send_result["message_id"],
        receiver_key_manager=bob_km,
        private_key=private_key,
    )

    print("RECEIVE RESULT:", recv_result)

    assert recv_result["content"] == "Hello Bob, quantum world!"
    print("✅ TEST PASSED")


if __name__ == "__main__":
    test_end_to_end()