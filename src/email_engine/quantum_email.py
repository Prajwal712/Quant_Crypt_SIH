"""
Quantum-Encrypted Email Engine
Integrates QKD, Key Management, and Encryption for secure email communication
"""
import json
import base64
from typing import Optional
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.errors import HttpError

from ..qkd.qkd_simulator import QKDChannel
from ..key_management.key_manager import KeyManager, KeyExchangeProtocol
from ..cryptography.security_levels import EncryptionEngine, SecurityLevel


class QuantumEmailEngine:
    """
    Complete email encryption engine with quantum key distribution
    """

    def __init__(self, gmail_service, sender_key_manager: KeyManager,
                 qkd_channel: QKDChannel, encryption_engine: EncryptionEngine):
        self.gmail_service = gmail_service
        self.sender_key_manager = sender_key_manager
        self.qkd_channel = qkd_channel
        self.encryption_engine = encryption_engine
        self.key_exchange = KeyExchangeProtocol(qkd_channel)

    def send_encrypted_email(self, sender: str, recipient: str, subject: str,
                           plaintext_content: str, security_level: SecurityLevel,
                           recipient_key_manager: KeyManager,
                           recipient_public_key=None) -> dict:
        """
        Send an encrypted email with specified security level

        Flow:
        1. Request quantum key from QKD channel
        2. Encrypt email content with selected security level
        3. Package encrypted data with metadata
        4. Send via Gmail API
        """

        # Step 1: Request quantum key via QKD
        key_id, quantum_key = self.key_exchange.request_key(
            self.sender_key_manager,
            recipient_key_manager,
            key_length=256
        )

        # Step 2: Encrypt email content
        plaintext_bytes = plaintext_content.encode('utf-8')

        ciphertext, metadata = self.encryption_engine.encrypt(
            plaintext_bytes,
            quantum_key,
            security_level,
            recipient_public_key
        )

        # Step 3: Create encrypted package
        encrypted_package = {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'key_id': key_id,
            'metadata': metadata,
            'sender_id': self.sender_key_manager.manager_id,
            'version': '1.0'
        }

        # Step 4: Create email message
        message = self._create_encrypted_message(
            sender,
            recipient,
            subject,
            encrypted_package
        )

        # Step 5: Send email
        try:
            sent_message = self.gmail_service.users().messages().send(
                userId='me',
                body=message
            ).execute()

            return {
                'status': 'success',
                'message_id': sent_message['id'],
                'key_id': key_id,
                'security_level': security_level.value,
                'encrypted_size': len(ciphertext)
            }

        except HttpError as error:
            return {
                'status': 'error',
                'error': str(error)
            }

    def receive_encrypted_email(self, message_id: str, receiver_key_manager: KeyManager,
                                private_key=None) -> dict:
        """
        Receive and decrypt an encrypted email

        Flow:
        1. Fetch email from Gmail
        2. Extract encrypted package
        3. Retrieve quantum key using key_id
        4. Decrypt content
        """

        try:
            # Step 1: Get email message
            msg = self.gmail_service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()

            # Step 2: Extract encrypted package
            payload = msg['payload']
            encrypted_package = self._extract_encrypted_package(payload)

            if not encrypted_package:
                return {
                    'status': 'error',
                    'error': 'Not a quantum-encrypted email'
                }

            # Step 3: Retrieve quantum key
            key_id = encrypted_package['key_id']
            quantum_key = receiver_key_manager.get_key(key_id)

            if not quantum_key:
                return {
                    'status': 'error',
                    'error': f'Quantum key {key_id} not found or expired'
                }

            # Step 4: Decrypt content
            ciphertext = base64.b64decode(encrypted_package['ciphertext'])
            metadata = encrypted_package['metadata']

            plaintext_bytes = self.encryption_engine.decrypt(
                ciphertext,
                quantum_key,
                metadata,
                private_key
            )

            plaintext = plaintext_bytes.decode('utf-8')

            # Extract headers
            headers = payload['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')

            return {
                'status': 'success',
                'sender': sender,
                'subject': subject,
                'content': plaintext,
                'security_level': metadata.get('security_level'),
                'key_id': key_id,
                'sender_id': encrypted_package.get('sender_id')
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def _create_encrypted_message(self, sender: str, recipient: str,
                                  subject: str, encrypted_package: dict) -> dict:
        """
        Create Gmail API message with encrypted package
        """
        message = MIMEMultipart()
        message['to'] = recipient
        message['from'] = sender
        message['subject'] = f"[QUANTUM-ENCRYPTED] {subject}"

        # Add encrypted package as JSON
        body_text = "This is a quantum-encrypted email. Use the quantum email client to decrypt.\n\n"
        body_text += "=== ENCRYPTED PACKAGE ===\n"
        body_text += json.dumps(encrypted_package, indent=2)

        message.attach(MIMEText(body_text, 'plain'))

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        return {'raw': raw_message}

    def _extract_encrypted_package(self, payload: dict) -> Optional[dict]:
        """
        Extract encrypted package from email payload
        """
        try:
            # Get email body
            if 'parts' in payload:
                part = payload['parts'][0]
                data = part['body']['data']
            else:
                data = payload['body']['data']

            # Decode body
            decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')

            # Extract JSON package
            if '=== ENCRYPTED PACKAGE ===' in decoded_data:
                package_start = decoded_data.index('===\n') + 4
                package_json = decoded_data[package_start:]
                return json.loads(package_json)

            return None

        except Exception:
            return None


class BulkEmailEncryption:
    """
    Handle bulk encrypted email operations
    """

    def __init__(self, quantum_email_engine: QuantumEmailEngine):
        self.engine = quantum_email_engine

    def send_bulk_encrypted(self, sender: str, recipients: list, subject: str,
                           content: str, security_level: SecurityLevel) -> list:
        """
        Send encrypted emails to multiple recipients
        """
        results = []

        for recipient_info in recipients:
            result = self.engine.send_encrypted_email(
                sender=sender,
                recipient=recipient_info['email'],
                subject=subject,
                plaintext_content=content,
                security_level=security_level,
                recipient_key_manager=recipient_info['key_manager'],
                recipient_public_key=recipient_info.get('public_key')
            )
            results.append({
                'recipient': recipient_info['email'],
                'result': result
            })

        return results
