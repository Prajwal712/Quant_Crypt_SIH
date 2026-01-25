"""
Key Management Module
Manages quantum keys with secure storage and lifecycle management.

ETSI GS QKD 014 aligned (conceptually)
QuKayDee-compatible architecture
"""

import secrets
import json
from typing import Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from threading import Lock


# =========================
# Key Manager (KME)
# =========================

class KeyManager:
    """
    Manages quantum keys with lifecycle:
    ACTIVE -> CONSUMED / EXPIRED -> CLEANED
    """

    def __init__(self, manager_id: str, storage_path: Optional[str] = None):
        self.manager_id = manager_id
        self.keys: Dict[str, dict] = {}
        self.lock = Lock()

        # Persistent storage
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path(f"./key_store/{manager_id}")

        self.storage_path.mkdir(parents=True, exist_ok=True)

    # -------------------------
    # Store Key
    # -------------------------

    def store_key(self, key: bytes, key_id: str, metadata: Optional[dict] = None) -> bool:
        """
        Store a quantum key (single-use).
        """
        with self.lock:
            if key_id in self.keys:
                return False

            entry = {
                "key_id": key_id,
                "key": key.hex(),
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                "usage_count": 0,
                "max_usage": 1,              # QKD keys are single-use
                "state": "ACTIVE",           # ACTIVE | CONSUMED | EXPIRED
                "metadata": metadata or {}
            }

            self.keys[key_id] = entry
            self._persist_key(key_id, entry)
            return True

    # -------------------------
    # Retrieve Key
    # -------------------------

    def get_key(self, key_id: str) -> Optional[dict]:
        """
        Retrieve a quantum key.
        Returns key material + metadata.
        """
        with self.lock:
            if key_id not in self.keys:
                self._load_key(key_id)

            if key_id not in self.keys:
                return None

            entry = self.keys[key_id]

            # Expiration check
            if datetime.utcnow() > datetime.fromisoformat(entry["expires_at"]):
                entry["state"] = "EXPIRED"
                self._persist_key(key_id, entry)
                return None

            # Usage check
            if entry["state"] != "ACTIVE":
                return None

            # Consume key
            entry["usage_count"] += 1
            entry["state"] = "CONSUMED"
            self._persist_key(key_id, entry)

            return {
                "key_id": key_id,
                "key": bytes.fromhex(entry["key"]),
                "metadata": entry["metadata"]
            }

    # -------------------------
    # Delete Key (secure)
    # -------------------------

    def delete_key(self, key_id: str) -> bool:
        """
        Securely delete a key (memory + disk).
        """
        with self.lock:
            if key_id not in self.keys:
                return False

            del self.keys[key_id]

            key_file = self.storage_path / f"{key_id}.key"
            if key_file.exists():
                with open(key_file, "wb") as f:
                    f.write(secrets.token_bytes(1024))
                key_file.unlink()

            return True

    # -------------------------
    # List Keys
    # -------------------------

    def list_keys(self) -> list:
        """
        List all keys with metadata (no key material).
        """
        with self.lock:
            return [
                {
                    "key_id": key_id,
                    "created_at": entry["created_at"],
                    "expires_at": entry["expires_at"],
                    "state": entry["state"],
                    "usage_count": entry["usage_count"],
                    "metadata": entry["metadata"]
                }
                for key_id, entry in self.keys.items()
            ]

    # -------------------------
    # Cleanup Expired Keys
    # -------------------------

    def cleanup_expired_keys(self) -> int:
        """
        Remove expired keys from memory and disk.
        """
        with self.lock:
            expired = []

            for key_id, entry in self.keys.items():
                if entry["state"] == "EXPIRED":
                    expired.append(key_id)

            for key_id in expired:
                self.delete_key(key_id)

            return len(expired)

    # -------------------------
    # Persistence Helpers
    # -------------------------

    def _persist_key(self, key_id: str, entry: dict):
        key_file = self.storage_path / f"{key_id}.key"
        with open(key_file, "w") as f:
            json.dump(entry, f)

    def _load_key(self, key_id: str):
        key_file = self.storage_path / f"{key_id}.key"
        if key_file.exists():
            with open(key_file, "r") as f:
                self.keys[key_id] = json.load(f)


# =========================
# Key Exchange Protocol
# =========================

class KeyExchangeProtocol:
    """
    Handles quantum key exchange between two KMEs.
    """

    def __init__(self, qkd_provider):
        self.qkd_provider = qkd_provider

    def request_key(
        self,
        sender_manager: KeyManager,
        receiver_manager: KeyManager,
        key_length: int = 256
    ) -> Tuple[str, bytes]:
        """
        Request a new quantum key pair.
        """

        key_id, quantum_key = self.qkd_provider.request_key(
            sender_manager.manager_id,
            receiver_manager.manager_id,
            key_length=key_length
        )

        sender_manager.store_key(
            quantum_key,
            key_id,
            {
                "peer": receiver_manager.manager_id,
                "purpose": "email_encryption",
                "key_length": key_length,
                "role": "sender"
            }
        )

        receiver_manager.store_key(
            quantum_key,
            key_id,
            {
                "peer": sender_manager.manager_id,
                "purpose": "email_encryption",
                "key_length": key_length,
                "role": "receiver"
            }
        )

        return key_id, quantum_key