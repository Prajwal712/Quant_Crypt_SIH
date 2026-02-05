"""
Key Management Module
Manages quantum keys with secure storage and lifecycle management.
ETSI GS QKD 014 aligned.
"""

import secrets
import json
from typing import Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from threading import Lock

# Import the new provider class
from src.qkd.qukaydee_provider import QuKayDeeProvider


KEY_USAGE_POLICY = {
    1: {"max_usage": 1},     # LEVEL_1_BASIC (OTP)
    2: {"max_usage": None},  # LEVEL_2_STANDARD (reusable)
    3: {"max_usage": 10},    # LEVEL_3_HIGH
    4: {"max_usage": 1},     # LEVEL_4_MAXIMUM
}

class KeyManager:
    """
    Manages quantum keys with lifecycle:
    ACTIVE -> CONSUMED / EXPIRED -> CLEANED
    """

    def __init__(
        self,
        manager_id: str,
        storage_path: Optional[str] = None,
        qkd_provider: Optional[QuKayDeeProvider] = None
    ):
        self.manager_id = manager_id
        self.qkd_provider = qkd_provider
        self.keys: Dict[str, dict] = {}
        self.lock = Lock()
        self._cached_key = None

        # Persistent storage setup
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path(f"./key_store/{manager_id}")

        self.storage_path.mkdir(parents=True, exist_ok=True)

    def get_cached_key(self, length: int = 32):
        """
        Returns a reusable symmetric key (AES).
        Used for Standard & Confidential modes.
        """
        if self._cached_key is None:
            self._cached_key = secrets.token_bytes(length)
        return self._cached_key

    # -------------------------
    # QKD Integration Methods
    # -------------------------

    def request_quantum_key(
        self,
        slave_sae_id: str,
        key_length: int = 256
    ) -> Tuple[str, bytes]:
        """
        Master SAE (Alice) requests a fresh quantum key from her KME.
        """
        if not self.qkd_provider:
            raise RuntimeError("No QKD provider configured for this KeyManager")

        # 1. Get from ETSI API
        key_id, key_bytes, meta = self.qkd_provider.request_key(
            sender_id=self.manager_id,
            receiver_id=slave_sae_id,
            key_size_bits=key_length
        )

        # 2. Store locally
        self.store_key(
            key_bytes,
            key_id,
            metadata={
                "peer_sae": slave_sae_id,
                "role": "master",
                "key_length": key_length,
                **meta,
            }
        )

        return key_id, key_bytes

    def retrieve_quantum_key(
        self,
        master_sae_id: str,
        key_id: str
    ) -> bytes:
        """
        Slave SAE (Bob) retrieves a specific key from his KME using the ID.
        """
        if not self.qkd_provider:
            raise RuntimeError("No QKD provider configured for this KeyManager")

        # 1. Get from ETSI API
        key_bytes, meta = self.qkd_provider.retrieve_key(
            sender_id=master_sae_id,
            key_id=key_id
        )

        # 2. Store locally
        self.store_key(
            key_bytes,
            key_id,
            metadata={
                "peer_sae": master_sae_id,
                "role": "slave",
                **meta,
            }
        )

        return key_bytes

    # -------------------------
    # Local Storage & Lifecycle
    # -------------------------

    def store_key(
        self,
        key: bytes,
        key_id: str,
        metadata: Optional[dict] = None,
        expires_in: Optional[int] = None
    ) -> bool:
        with self.lock:
            if key_id in self.keys:
                return False

            expires_at = (
                datetime.utcnow() + timedelta(seconds=expires_in)
                if expires_in
                else datetime.utcnow() + timedelta(minutes=10)
            )

            entry = {
                "key_id": key_id,
                "key": key.hex(),
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": expires_at.isoformat(),
                "usage_count": 0,
                "state": "ACTIVE",
                "metadata": metadata or {},
                "max_usage": metadata.get("max_usage") if metadata else None,
            }

            self.keys[key_id] = entry
            self._persist_key(key_id, entry)
            return True

    def get_key(self, key_id: str) -> Optional[dict]:
        with self.lock:
            if key_id not in self.keys:
                self._load_key(key_id)

            if key_id not in self.keys:
                return None

            entry = self.keys[key_id]

            if datetime.utcnow() > datetime.fromisoformat(entry["expires_at"]):
                entry["state"] = "EXPIRED"
                self._persist_key(key_id, entry)
                return None

            if entry["state"] != "ACTIVE":
                return None

            entry["usage_count"] += 1
            max_usage = entry.get("max_usage")

            if max_usage is not None and entry["usage_count"] >= max_usage:
                entry["state"] = "CONSUMED"
            else:
                entry["state"] = "ACTIVE"
            self._persist_key(key_id, entry)

            return {
                "key_id": key_id,
                "key": bytes.fromhex(entry["key"]),
                "metadata": entry["metadata"]
            }

    def delete_key(self, key_id: str) -> bool:
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

    def _persist_key(self, key_id: str, entry: dict):
        key_file = self.storage_path / f"{key_id}.key"
        with open(key_file, "w") as f:
            json.dump(entry, f)

    def _load_key(self, key_id: str):
        key_file = self.storage_path / f"{key_id}.key"
        if key_file.exists():
            with open(key_file, "r") as f:
                self.keys[key_id] = json.load(f)