"""
Quantum-Encrypted Email Engine
ETSI GS QKD 014 compliant
Uses QuKayDee-backed KeyManager + QKD-aware encryption
"""

import json
import base64
from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from googleapiclient.errors import HttpError

from ..key_management.key_manager import KeyManager
from ..cryptography.security_levels import EncryptionEngine, SecurityLevel


class QuantumEmailEngine:
    """
    Quantum-secure email engine using ETSI QKD (QuKayDee).
    """

    def __init__(
        self,
        gmail_service,
        sender_key_manager: KeyManager,
        encryption_engine: EncryptionEngine,
    ):
        self.gmail_service = gmail_service
        self.sender_key_manager = sender_key_manager
        self.encryption_engine = encryption_engine

    # ==========================================================
    # SEND
    # ==========================================================

    def send_encrypted_email(
        self,
        sender: str,
        recipient: str,
        subject: str,
        plaintext_content: str,
        security_level: SecurityLevel,
        recipient_key_manager: KeyManager,
        recipient_public_key=None,
    ) -> dict:
        """
        Send a quantum-encrypted email.

        Flow:
        1. ETSI enc_keys via KeyManager
        2. Encrypt payload
        3. Send via Gmail API
        """

        try:
            # 1️⃣ Request quantum key (ETSI enc_keys)
            key_id, quantum_key = self.sender_key_manager.request_quantum_key(
                slave_sae_id=recipient_key_manager.manager_id,
                key_length=256
            )

            # 2️⃣ Encrypt message
            plaintext_bytes = plaintext_content.encode("utf-8")

            ciphertext, crypto_metadata = self.encryption_engine.encrypt(
                plaintext_bytes,
                quantum_key,
                security_level,
                recipient_public_key,
            )

            # 3️⃣ Build encrypted package
            encrypted_package = {
                "ciphertext": base64.b64encode(ciphertext).decode("utf-8"),
                "key_id": key_id,
                "metadata": crypto_metadata,
                "sender_id": self.sender_key_manager.manager_id,
                "protocol": "ETSI-GS-QKD-014",
                "version": "1.0",
            }

            # 4️⃣ Create email
            message = self._create_encrypted_message(
                sender,
                recipient,
                subject,
                encrypted_package,
            )

            # 5️⃣ Send
            sent = (
                self.gmail_service.users()
                .messages()
                .send(userId="me", body=message)
                .execute()
            )

            return {
                "status": "success",
                "message_id": sent["id"],
                "key_id": key_id,
                "security_level": security_level.value,
                "ciphertext_bytes": len(ciphertext),
            }

        except HttpError as e:
            return {"status": "error", "error": str(e)}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ==========================================================
    # RECEIVE
    # ==========================================================

    def receive_encrypted_email(
        self,
        message_id: str,
        receiver_key_manager: KeyManager,
        private_key=None,
    ) -> dict:
        """
        Receive and decrypt a quantum-encrypted email.

        Flow:
        1. Fetch email
        2. Extract encrypted package
        3. ETSI dec_keys via KeyManager
        4. Decrypt payload
        """

        try:
            # 1️⃣ Fetch email
            msg = (
                self.gmail_service.users()
                .messages()
                .get(userId="me", id=message_id)
                .execute()
            )

            payload = msg["payload"]

            # 2️⃣ Extract encrypted package
            encrypted_package = self._extract_encrypted_package(payload)

            if not encrypted_package:
                return {
                    "status": "error",
                    "error": "Not a quantum-encrypted email",
                }

            key_id = encrypted_package["key_id"]
            sender_id = encrypted_package["sender_id"]

            # 3️⃣ Retrieve quantum key (ETSI dec_keys)
            quantum_key = receiver_key_manager.retrieve_quantum_key(
                master_sae_id=sender_id,
                key_id=key_id,
            )

            if not quantum_key:
                return {
                    "status": "error",
                    "error": f"Quantum key {key_id} not found or expired",
                }

            # 4️⃣ Decrypt
            ciphertext = base64.b64decode(encrypted_package["ciphertext"])
            metadata = encrypted_package["metadata"]

            plaintext_bytes = self.encryption_engine.decrypt(
                ciphertext,
                quantum_key,
                metadata,
                private_key,
            )

            plaintext = plaintext_bytes.decode("utf-8")

            headers = payload.get("headers")
            if not isinstance(headers, list):
                headers = []

            subject = "No Subject"
            sender = "Unknown"

            for h in headers:
                if h.get("name") == "Subject":
                    subject = h.get("value", subject)
                elif h.get("name") == "From":
                    sender = h.get("value", sender)

            return {
                "status": "success",
                "sender": sender,
                "subject": subject,
                "content": plaintext,
                "security_level": metadata.get("security_level"),
                "key_id": key_id,
                "sender_id": sender_id,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    # ==========================================================
    # EMAIL HELPERS
    # ==========================================================

    def _create_encrypted_message(
        self,
        sender: str,
        recipient: str,
        subject: str,
        encrypted_package: dict,
    ) -> dict:
        """
        Create Gmail API message with encrypted payload.
        """

        message = MIMEMultipart()
        message["to"] = recipient
        message["from"] = sender
        message["subject"] = f"[QUANTUM-ENCRYPTED] {subject}"

        body = (
            "This email is protected using Quantum Key Distribution (ETSI GS QKD 014).\n\n"
            "=== ENCRYPTED PACKAGE ===\n"
            + json.dumps(encrypted_package, indent=2)
        )

        message.attach(MIMEText(body, "plain"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        return {"raw": raw}

    def _extract_encrypted_package(self, payload: dict) -> Optional[dict]:
        try:
            # 1️⃣ Extract body data
            if "parts" in payload and payload["parts"]:
                data = payload["parts"][0]["body"]["data"]
            else:
                data = payload["body"]["data"]

            # 2️⃣ Decode base64
            decoded = base64.urlsafe_b64decode(data).decode("utf-8")

            # 3️⃣ Locate encrypted package marker
            marker = "=== ENCRYPTED PACKAGE ==="
            marker_idx = decoded.find(marker)
            if marker_idx == -1:
                return None

            # 4️⃣ Extract text AFTER marker
            after_marker = decoded[marker_idx + len(marker):]

            # 5️⃣ Find JSON object boundaries safely
            json_start = after_marker.find("{")
            json_end = after_marker.rfind("}")

            if json_start == -1 or json_end == -1:
                return None

            json_str = after_marker[json_start: json_end + 1]

            # 6️⃣ Parse clean JSON only
            return json.loads(json_str)

        except Exception as e:
            print("PACKAGE EXTRACT ERROR:", e)
            return None