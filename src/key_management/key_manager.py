"""
Key Management Module
Manages quantum keys with secure storage and REST API access
"""
import secrets
import json
import time
from typing import Dict, Optional, Tuple
from pathlib import Path
import hashlib
from datetime import datetime, timedelta
from threading import Lock

class KeyManager:
    """
    Manages quantum keys with lifecycle management
    """
    def __init__(self, manager_id: str, storage_path: Optional[str] = None):
        self.manager_id = manager_id
        self.keys: Dict[str, dict] = {}
        self.lock = Lock()

        # Storage path for key persistence
        if storage_path:
            self.storage_path = Path(storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)
        else:
            self.storage_path = Path(f"./key_store/{manager_id}")
            self.storage_path.mkdir(parents=True, exist_ok=True)

    def store_key(self, key: bytes, key_id: str, metadata: Optional[dict] = None) -> bool:
        """
        Store a quantum key with metadata
        """
        with self.lock:
            if key_id in self.keys:
                return False

            key_entry = {
                'key': key.hex(),
                'key_id': key_id,
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
                'usage_count': 0,
                'max_usage': 2,  # One-time pad principle for quantum keys
                'metadata': metadata or {}
            }

            self.keys[key_id] = key_entry
            self._persist_key(key_id, key_entry)
            return True

    def get_key(self, key_id: str) -> Optional[bytes]:
        """
        Retrieve a quantum key by ID
        """
        with self.lock:
            if key_id not in self.keys:
                # Try loading from disk
                self._load_key(key_id)

            if key_id not in self.keys:
                return None

            key_entry = self.keys[key_id]

            # Check expiration
            expires_at = datetime.fromisoformat(key_entry['expires_at'])
            if datetime.now() > expires_at:
                self.delete_key(key_id)
                return None

            # Check usage limit
            if key_entry['usage_count'] >= key_entry['max_usage']:
                return None

            # Increment usage count
            key_entry['usage_count'] += 1

            # If max usage reached, mark for deletion
            if key_entry['usage_count'] >= key_entry['max_usage']:
                self.delete_key(key_id)

            return bytes.fromhex(key_entry['key'])

    def delete_key(self, key_id: str) -> bool:
        """
        Securely delete a quantum key
        """
        with self.lock:
            if key_id in self.keys:
                # Remove from memory
                del self.keys[key_id]

                # Remove from disk
                key_file = self.storage_path / f"{key_id}.key"
                if key_file.exists():
                    # Overwrite before deletion for security
                    with open(key_file, 'wb') as f:
                        f.write(secrets.token_bytes(1024))
                    key_file.unlink()

                return True
            return False

    def list_keys(self) -> list:
        """
        List all available keys with metadata
        """
        with self.lock:
            return [
                {
                    'key_id': key_id,
                    'created_at': entry['created_at'],
                    'expires_at': entry['expires_at'],
                    'usage_count': entry['usage_count'],
                    'metadata': entry['metadata']
                }
                for key_id, entry in self.keys.items()
            ]

    def _persist_key(self, key_id: str, key_entry: dict):
        """
        Persist key to disk (encrypted storage in production)
        """
        key_file = self.storage_path / f"{key_id}.key"
        with open(key_file, 'w') as f:
            json.dump(key_entry, f)

    def _load_key(self, key_id: str):
        """
        Load key from disk
        """
        key_file = self.storage_path / f"{key_id}.key"
        if key_file.exists():
            with open(key_file, 'r') as f:
                self.keys[key_id] = json.load(f)

    def cleanup_expired_keys(self):
        """
        Remove all expired keys
        """
        with self.lock:
            expired_keys = []
            for key_id, entry in self.keys.items():
                expires_at = datetime.fromisoformat(entry['expires_at'])
                if datetime.now() > expires_at:
                    expired_keys.append(key_id)

            for key_id in expired_keys:
                self.delete_key(key_id)

            return len(expired_keys)


class KeyExchangeProtocol:
    """
    Handles key exchange between two Key Managers
    """
    def __init__(self, qkd_channel):
        self.qkd_channel = qkd_channel

    def request_key(self, sender_manager: KeyManager, receiver_manager: KeyManager,
                   key_length: int = 256) -> Tuple[str, bytes]:
        """
        Request a new quantum key pair for communication
        Returns: (key_id, quantum_key)
        """
        # Establish quantum key via QKD channel
        quantum_key, key_id = self.qkd_channel.establish_key_pair(
            sender_manager.manager_id,
            receiver_manager.manager_id
        )

        # Store key in both managers
        metadata = {
            'peer': receiver_manager.manager_id,
            'purpose': 'email_encryption',
            'key_length': key_length
        }
        sender_manager.store_key(quantum_key, key_id, metadata)

        metadata['peer'] = sender_manager.manager_id
        receiver_manager.store_key(quantum_key, key_id, metadata)

        return key_id, quantum_key
