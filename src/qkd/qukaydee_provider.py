"""
QuKayDee QKD Provider
ETSI GS QKD 014 v1.1.1 compliant client

This provider integrates QuKayDee (cloud QKD simulator)
as a Key Management backend using mutual TLS.
"""

from __future__ import annotations

import base64

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

import requests
from requests import Response

from src.qkd.provider import QKDProvider


# =========================
# Exceptions
# =========================

class QuKayDeeError(Exception):
    """Base exception for QuKayDee provider."""


class QuKayDeeHTTPError(QuKayDeeError):
    """HTTP-level failure."""


class QuKayDeeAPIError(QuKayDeeError):
    """ETSI QKD 014 API-level error."""


# =========================
# Config
# =========================

@dataclass
class QuKayDeeConfig:
    """
    Runtime configuration for QuKayDee.

    ALL paths are placeholders until real certs are added.
    """
    account_id: str

    # KME + SAE identity
    kme_id: str          # e.g. "kme-1" or "kme-2"
    sae_id: str          # e.g. "sae-1" or "sae-2"

    # TLS assets
    server_ca_cert: str  # account-<ACCOUNT_ID>-server-ca-qukaydee-com.crt
    sae_cert: str        # sae-1.crt or sae-2.crt
    sae_key: str         # sae-1.key or sae-2.key

    # Defaults
    timeout_seconds: int = 10

    @property
    def base_url(self) -> str:
        return (
            f"https://{self.kme_id}.acct-{self.account_id}"
            f".etsi-qkd-api.qukaydee.com/api/v1"
        )


# =========================
# Low-level ETSI QKD client
# =========================

class QuKayDeeClient:
    """
    Thin ETSI GS QKD 014 REST client.
    """

    def __init__(self, cfg: QuKayDeeConfig):
        self.cfg = cfg

    # ---------- helpers ----------

    def _request(
        self,
        method: str,
        path: str,
        params: Dict | None = None,
    ) -> Dict:
        url = self.cfg.base_url + path

        try:
            resp: Response = requests.request(
                method=method,
                url=url,
                params=params,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                cert=(self.cfg.sae_cert, self.cfg.sae_key),
                verify=self.cfg.server_ca_cert,
                timeout=self.cfg.timeout_seconds,
            )
        except requests.RequestException as e:
            raise QuKayDeeHTTPError(str(e)) from e

        if not resp.ok:
            raise QuKayDeeHTTPError(
                f"HTTP {resp.status_code}: {resp.text}"
            )

        data = resp.json()

        # ETSI error model
        if "error" in data:
            raise QuKayDeeAPIError(str(data["error"]))

        if "errors" in data and data["errors"]:
            raise QuKayDeeAPIError(str(data["errors"]))

        return data

    # ---------- ETSI endpoints ----------

    def get_status(self, slave_sae_id: str) -> Dict:
        """
        GET /keys/{slave_sae_id}/status
        """
        return self._request(
            "GET",
            f"/keys/{slave_sae_id}/status",
        )

    def get_keys(
        self,
        slave_sae_id: str,
        number: int,
        size_bits: int,
    ) -> List[Dict]:
        """
        POST /keys/{slave_sae_id}/enc_keys
        """
        data = self._request(
            "POST",
            f"/keys/{slave_sae_id}/enc_keys",
            params={"number": number, "size": size_bits},
        )
        return data.get("keys", [])

    def get_keys_by_id(
        self,
        master_sae_id: str,
        key_ids: List[str],
    ) -> List[Dict]:
        """
        GET /keys/{master_sae_id}/dec_keys
        """
        keys: List[Dict] = []

        for key_id in key_ids:
            data = self._request(
                "GET",
                f"/keys/{master_sae_id}/dec_keys",
                params={"key_ID": key_id},
            )
            keys.extend(data.get("keys", []))

        return keys


# =========================
# High-level Provider
# =========================

class QuKayDeeProvider(QKDProvider):
    """
    High-level QKDProvider implementation used by MailQ.

    This class enforces:
    - Correct call sequence
    - Key ID propagation
    - Base64 decoding
    """

    def __init__(self, config: QuKayDeeConfig):
        self.cfg = config
        self.client = QuKayDeeClient(config)

    # ---------- Master SAE (Sender) ----------

    """
    NOTE: sender_id is validated implicitly via mTLS certificate.
    It is not sent over the wire per ETSI QKD 014.
    """

    def request_key(
        self,
        sender_id: str,
        receiver_id: str,
        key_size_bits: int = 1024,
    ) -> Tuple[str, bytes, Dict]:
        """
        Master SAE flow:
        1. Status
        2. enc_keys
        3. Return (key_id, key_bytes)
        """

        if sender_id != self.cfg.sae_id:
            raise QuKayDeeError(
                f"Configured SAE ({self.cfg.sae_id}) cannot act as {sender_id}"
            )

        # 1️⃣ Status check
        status = self.client.get_status(receiver_id)

        if status.get("stored_key_count", 0) <= 0:
            raise QuKayDeeError("No keys available in key stream")

        max_size = status.get("max_key_size", key_size_bits)
        if key_size_bits > max_size:
            raise QuKayDeeError(
                f"Requested key too large ({key_size_bits} > {max_size})"
            )

        # 2️⃣ Request key
        keys = self.client.get_keys(
            slave_sae_id=receiver_id,
            number=1,
            size_bits=key_size_bits,
        )

        if not keys:
            raise QuKayDeeError("No keys returned by enc_keys")

        key_entry = keys[0]
        key_id = key_entry["key_ID"]
        key_b64 = key_entry["key"]

        # 3️⃣ Decode key material
        try:
            key_bytes = base64.b64decode(key_b64)
        except Exception as e:
            raise QuKayDeeError("Invalid Base64 key") from e

        expires_in = status.get("key_expiry_time", 600)

        return key_id, key_bytes, {
            "expires_in": expires_in,
            "source": "qukaydee",
            "standard": "ETSI-GS-QKD-014"
        }

    # ---------- Slave SAE (Receiver) ----------

    """
    NOTE: sender_id is validated implicitly via mTLS certificate.
    It is not sent over the wire per ETSI QKD 014.
    """


    def retrieve_key(
        self,
        sender_id: str,
        key_id: str,
    ) -> Tuple[bytes, Dict]:
        """
        Slave SAE flow:
        dec_keys using key_ID
        """

        if self.cfg.sae_id == sender_id:
            raise QuKayDeeError(
                "Slave SAE cannot retrieve keys it originally requested"
            )

        keys = self.client.get_keys_by_id(
            master_sae_id=sender_id,
            key_ids=[key_id],
        )

        if not keys:
            raise QuKayDeeError("Key not found or expired")

        key_b64 = keys[0]["key"]

        try:
            key_bytes = base64.b64decode(key_b64)
        except Exception as e:
            raise QuKayDeeError("Invalid Base64 key") from e

        return key_bytes, {
            "source": "qukaydee",
            "standard": "ETSI-GS-QKD-014"
        }