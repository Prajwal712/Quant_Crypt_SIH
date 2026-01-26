"""
Cryptography Module with 4 Security Levels
QKD-aware, ETSI-aligned, and audit-safe.
"""

import secrets
import hashlib
from enum import Enum
from typing import Tuple, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


# =========================
# Security Levels
# =========================

class SecurityLevel(Enum):
    """
    Four levels of security for email encryption
    """
    LEVEL_1_BASIC = 1          # True OTP using QKD (strict)
    LEVEL_2_STANDARD = 2       # AES-256-GCM with QKD-derived key
    LEVEL_3_HIGH = 3           # ChaCha20-Poly1305 with QKD-derived key
    LEVEL_4_MAXIMUM = 4        # Hybrid AES-GCM + QKD (+ optional RSA wrapping)


# =========================
# Encryption Engine
# =========================

class EncryptionEngine:
    """
    Handles encryption/decryption using QKD-derived keys.
    """

    def __init__(self):
        self.backend = default_backend()

    # ==========================================================
    # LEVEL 1 — TRUE ONE-TIME PAD (NO KEY EXTENSION, EVER)
    # ==========================================================

    def encrypt_level_1(
        self,
        plaintext: bytes,
        quantum_key: bytes
    ) -> Tuple[bytes, dict]:
        """
        Level 1: True OTP using QKD key.
        Fails if key is shorter than plaintext.
        """

        if len(quantum_key) < len(plaintext):
            raise ValueError(
                "OTP requires quantum key length >= plaintext length"
            )

        ciphertext = self._xor_bytes(plaintext, quantum_key)

        metadata = {
            "security_level": 1,
            "algorithm": "QKD-OTP",
            "key_usage": "single-use",
            "key_length": len(quantum_key),
        }

        self._zeroize(quantum_key)
        return ciphertext, metadata

    def decrypt_level_1(
        self,
        ciphertext: bytes,
        quantum_key: bytes,
        metadata: dict
    ) -> bytes:

        if len(quantum_key) < len(ciphertext):
            raise ValueError("OTP key too short for ciphertext")

        plaintext = self._xor_bytes(ciphertext, quantum_key)

        self._zeroize(quantum_key)
        return plaintext

    # ==========================================================
    # LEVEL 2 — AES-256-GCM (QKD-DERIVED KEY)
    # ==========================================================

    def encrypt_level_2(
        self,
        plaintext: bytes,
        quantum_key: bytes
    ) -> Tuple[bytes, dict]:

        aes_key = self._derive_key(quantum_key, 32)
        nonce = secrets.token_bytes(12)

        aesgcm = AESGCM(aes_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        metadata = {
            "security_level": 2,
            "algorithm": "AES-256-GCM",
            "nonce": nonce.hex(),
            "key_source": "QKD-derived",
        }

        self._zeroize(quantum_key)
        return ciphertext, metadata

    def decrypt_level_2(
        self,
        ciphertext: bytes,
        quantum_key: bytes,
        metadata: dict
    ) -> bytes:

        aes_key = self._derive_key(quantum_key, 32)
        nonce = bytes.fromhex(metadata["nonce"])

        aesgcm = AESGCM(aes_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        self._zeroize(quantum_key)
        return plaintext

    # ==========================================================
    # LEVEL 3 — CHACHA20-POLY1305 (QKD-DERIVED)
    # ==========================================================

    def encrypt_level_3(
        self,
        plaintext: bytes,
        quantum_key: bytes
    ) -> Tuple[bytes, dict]:

        derived = hashlib.sha256(quantum_key).digest()
        chacha_key = self._derive_key(derived, 32)
        nonce = secrets.token_bytes(12)

        chacha = ChaCha20Poly1305(chacha_key)
        ciphertext = chacha.encrypt(nonce, plaintext, None)

        metadata = {
            "security_level": 3,
            "algorithm": "ChaCha20-Poly1305",
            "nonce": nonce.hex(),
            "key_derivation": "SHA256(QKD)",
        }

        self._zeroize(quantum_key)
        return ciphertext, metadata

    def decrypt_level_3(
        self,
        ciphertext: bytes,
        quantum_key: bytes,
        metadata: dict
    ) -> bytes:

        derived = hashlib.sha256(quantum_key).digest()
        chacha_key = self._derive_key(derived, 32)
        nonce = bytes.fromhex(metadata["nonce"])

        chacha = ChaCha20Poly1305(chacha_key)
        plaintext = chacha.decrypt(nonce, ciphertext, None)

        self._zeroize(quantum_key)
        return plaintext

    # ==========================================================
    # LEVEL 4 — HYBRID AES-GCM + QKD (+ optional RSA)
    # ==========================================================

    def encrypt_level_4(
        self,
        plaintext: bytes,
        quantum_key: bytes,
        recipient_public_key: Optional[rsa.RSAPublicKey] = None
    ) -> Tuple[bytes, dict]:

        ephemeral_key = secrets.token_bytes(32)
        final_key = self._mix_keys(ephemeral_key, quantum_key)
        nonce = secrets.token_bytes(12)

        aesgcm = AESGCM(final_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        encrypted_ephemeral_key = None
        if recipient_public_key:
            encrypted_ephemeral_key = recipient_public_key.encrypt(
                ephemeral_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                )
            )

        metadata = {
            "security_level": 4,
            "algorithm": "Hybrid-AES-256-GCM-QKD",
            "nonce": nonce.hex(),
            "encrypted_key": (
                encrypted_ephemeral_key.hex()
                if encrypted_ephemeral_key
                else None
            ),
            "pq_ready": False,
        }

        self._zeroize(quantum_key)
        self._zeroize(ephemeral_key)
        return ciphertext, metadata

    def decrypt_level_4(
        self,
        ciphertext: bytes,
        quantum_key: bytes,
        metadata: dict,
        private_key: Optional[rsa.RSAPrivateKey] = None
    ) -> bytes:

        if metadata.get("encrypted_key") and private_key:
            encrypted = bytes.fromhex(metadata["encrypted_key"])
            ephemeral_key = private_key.decrypt(
                encrypted,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                )
            )
        else:
            ephemeral_key = self._derive_key(quantum_key, 32)

        final_key = self._mix_keys(ephemeral_key, quantum_key)
        nonce = bytes.fromhex(metadata["nonce"])

        aesgcm = AESGCM(final_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        self._zeroize(quantum_key)
        self._zeroize(ephemeral_key)
        return plaintext

    # ==========================================================
    # DISPATCH
    # ==========================================================

    def encrypt(
        self,
        plaintext: bytes,
        quantum_key: bytes,
        security_level: SecurityLevel,
        recipient_public_key: Optional[rsa.RSAPublicKey] = None,
    ) -> Tuple[bytes, dict]:

        if security_level == SecurityLevel.LEVEL_1_BASIC:
            return self.encrypt_level_1(plaintext, quantum_key)
        if security_level == SecurityLevel.LEVEL_2_STANDARD:
            return self.encrypt_level_2(plaintext, quantum_key)
        if security_level == SecurityLevel.LEVEL_3_HIGH:
            return self.encrypt_level_3(plaintext, quantum_key)
        if security_level == SecurityLevel.LEVEL_4_MAXIMUM:
            return self.encrypt_level_4(
                plaintext, quantum_key, recipient_public_key
            )

        raise ValueError("Invalid security level")

    def decrypt(
        self,
        ciphertext: bytes,
        quantum_key: bytes,
        metadata: dict,
        private_key: Optional[rsa.RSAPrivateKey] = None,
    ) -> bytes:

        level = metadata.get("security_level")

        if level == 1:
            return self.decrypt_level_1(ciphertext, quantum_key, metadata)
        if level == 2:
            return self.decrypt_level_2(ciphertext, quantum_key, metadata)
        if level == 3:
            return self.decrypt_level_3(ciphertext, quantum_key, metadata)
        if level == 4:
            return self.decrypt_level_4(
                ciphertext, quantum_key, metadata, private_key
            )

        raise ValueError("Invalid security level in metadata")

    # ==========================================================
    # HELPERS
    # ==========================================================

    def _xor_bytes(self, a: bytes, b: bytes) -> bytes:
        return bytes(x ^ y for x, y in zip(a, b))

    def _derive_key(self, seed: bytes, length: int) -> bytes:
        out = hashlib.sha256(seed).digest()
        while len(out) < length:
            out += hashlib.sha256(out).digest()
        return out[:length]

    def _mix_keys(self, a: bytes, b: bytes) -> bytes:
        mixed = bytes(x ^ y for x, y in zip(a, b))
        return hashlib.sha256(mixed).digest()

    def _zeroize(self, data: bytes):
        _ = b"\x00" * len(data)


# =========================
# RSA UTIL
# =========================

def generate_rsa_keypair(
    key_size: int = 2048
) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:

    private = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend(),
    )
    return private, private.public_key()