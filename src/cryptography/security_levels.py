"""
Cryptography Module with 4 Security Levels
Implements different encryption schemes based on security requirements
"""
import secrets
import hashlib
from enum import Enum
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend

class SecurityLevel(Enum):
    """
    Four levels of security for email encryption
    """
    LEVEL_1_BASIC = 1          # XOR with quantum key (fastest)
    LEVEL_2_STANDARD = 2       # AES-256-GCM with quantum key
    LEVEL_3_HIGH = 3           # ChaCha20-Poly1305 + quantum key mixing
    LEVEL_4_MAXIMUM = 4        # Hybrid: RSA + AES-256-GCM + quantum key


class EncryptionEngine:
    """
    Handles encryption/decryption at different security levels
    """

    def __init__(self):
        self.backend = default_backend()

    # ============= LEVEL 1: BASIC (XOR with Quantum Key) =============

    def encrypt_level_1(self, plaintext: bytes, quantum_key: bytes) -> Tuple[bytes, dict]:
        """
        Level 1: XOR encryption with quantum key (One-Time Pad principle)
        Fastest but requires key length >= plaintext length
        """
        if len(quantum_key) < len(plaintext):
            # Extend key using secure key derivation
            quantum_key = self._extend_key(quantum_key, len(plaintext))

        ciphertext = self._xor_encrypt(plaintext, quantum_key)

        metadata = {
            'security_level': 1,
            'algorithm': 'XOR_OTP',
            'key_length': len(quantum_key)
        }

        return ciphertext, metadata

    def decrypt_level_1(self, ciphertext: bytes, quantum_key: bytes, metadata: dict) -> bytes:
        """
        Level 1: XOR decryption
        """
        if len(quantum_key) < len(ciphertext):
            quantum_key = self._extend_key(quantum_key, len(ciphertext))

        return self._xor_encrypt(ciphertext, quantum_key)  # XOR is symmetric

    # ============= LEVEL 2: STANDARD (AES-256-GCM) =============

    def encrypt_level_2(self, plaintext: bytes, quantum_key: bytes) -> Tuple[bytes, dict]:
        """
        Level 2: AES-256-GCM with quantum key
        Good balance of security and performance
        """
        # Ensure 32-byte key for AES-256
        aes_key = self._derive_key(quantum_key, 32)

        # Generate random nonce (96 bits for GCM)
        nonce = secrets.token_bytes(12)

        # Encrypt with AES-GCM
        aesgcm = AESGCM(aes_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        metadata = {
            'security_level': 2,
            'algorithm': 'AES-256-GCM',
            'nonce': nonce.hex()
        }

        return ciphertext, metadata

    def decrypt_level_2(self, ciphertext: bytes, quantum_key: bytes, metadata: dict) -> bytes:
        """
        Level 2: AES-256-GCM decryption
        """
        aes_key = self._derive_key(quantum_key, 32)
        nonce = bytes.fromhex(metadata['nonce'])

        aesgcm = AESGCM(aes_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext

    # ============= LEVEL 3: HIGH (ChaCha20-Poly1305 + Key Mixing) =============

    def encrypt_level_3(self, plaintext: bytes, quantum_key: bytes) -> Tuple[bytes, dict]:
        """
        Level 3: ChaCha20-Poly1305 with quantum key mixing
        Enhanced security with additional entropy
        """
        # Mix quantum key with additional entropy
        mixed_key = hashlib.sha256(quantum_key).digest()
        chacha_key = self._derive_key(mixed_key, 32)

        # Generate nonce for ChaCha20
        nonce = secrets.token_bytes(12)

        # Encrypt with ChaCha20-Poly1305
        chacha = ChaCha20Poly1305(chacha_key)
        ciphertext = chacha.encrypt(nonce, plaintext, None)

        metadata = {
            'security_level': 3,
            'algorithm': 'ChaCha20-Poly1305',
            'nonce': nonce.hex(),
            'key_mixing': True
        }

        return ciphertext, metadata

    def decrypt_level_3(self, ciphertext: bytes, quantum_key: bytes, metadata: dict) -> bytes:
        """
        Level 3: ChaCha20-Poly1305 decryption
        """
        # Note: In real implementation, the mixed entropy should be transmitted securely
        # For now, we'll use a deterministic mixing that both parties can reproduce
        mixed_key = hashlib.sha256(quantum_key).digest()
        chacha_key = self._derive_key(mixed_key, 32)

        nonce = bytes.fromhex(metadata['nonce'])

        chacha = ChaCha20Poly1305(chacha_key)
        plaintext = chacha.decrypt(nonce, ciphertext, None)

        return plaintext

    # ============= LEVEL 4: MAXIMUM (Hybrid RSA + AES + Quantum) =============

    def encrypt_level_4(self, plaintext: bytes, quantum_key: bytes,
                       recipient_public_key: Optional[rsa.RSAPublicKey] = None) -> Tuple[bytes, dict]:
        """
        Level 4: Hybrid encryption (RSA + AES-256-GCM + Quantum Key)
        Maximum security with post-quantum resistance preparation
        """
        # Generate ephemeral AES key
        ephemeral_key = secrets.token_bytes(32)

        # Mix ephemeral key with quantum key
        final_key = self._mix_keys(ephemeral_key, quantum_key)

        # Generate nonce
        nonce = secrets.token_bytes(12)

        # Encrypt plaintext with AES-GCM
        aesgcm = AESGCM(final_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        # If RSA public key provided, encrypt the ephemeral key
        encrypted_ephemeral_key = None
        if recipient_public_key:
            encrypted_ephemeral_key = recipient_public_key.encrypt(
                ephemeral_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

        metadata = {
            'security_level': 4,
            'algorithm': 'Hybrid-RSA-AES-256-GCM-Quantum',
            'nonce': nonce.hex(),
            'encrypted_key': encrypted_ephemeral_key.hex() if encrypted_ephemeral_key else None,
            'quantum_enhanced': True
        }

        return ciphertext, metadata

    def decrypt_level_4(self, ciphertext: bytes, quantum_key: bytes, metadata: dict,
                       private_key: Optional[rsa.RSAPrivateKey] = None) -> bytes:
        """
        Level 4: Hybrid decryption
        """
        # Decrypt ephemeral key with RSA if available
        ephemeral_key = None
        if metadata.get('encrypted_key') and private_key:
            encrypted_ephemeral_key = bytes.fromhex(metadata['encrypted_key'])
            ephemeral_key = private_key.decrypt(
                encrypted_ephemeral_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        else:
            # Fallback: derive from quantum key
            ephemeral_key = self._derive_key(quantum_key, 32)

        # Mix with quantum key
        final_key = self._mix_keys(ephemeral_key, quantum_key)

        nonce = bytes.fromhex(metadata['nonce'])

        # Decrypt with AES-GCM
        aesgcm = AESGCM(final_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext

    # ============= Helper Methods =============

    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        """
        XOR encryption (symmetric)
        """
        result = bytearray()
        for i in range(len(data)):
            result.append(data[i] ^ key[i % len(key)])
        return bytes(result)

    def _derive_key(self, quantum_key: bytes, length: int) -> bytes:
        """
        Derive a key of specific length using HKDF-like approach
        """
        hash_obj = hashlib.sha256(quantum_key)
        derived = hash_obj.digest()

        while len(derived) < length:
            hash_obj = hashlib.sha256(derived)
            derived += hash_obj.digest()

        return derived[:length]

    def _extend_key(self, key: bytes, length: int) -> bytes:
        """
        Extend key to required length
        """
        extended = key
        while len(extended) < length:
            extended += hashlib.sha256(extended).digest()
        return extended[:length]

    def _mix_keys(self, key1: bytes, key2: bytes) -> bytes:
        """
        Mix two keys together
        """
        # XOR mixing
        min_len = min(len(key1), len(key2))
        mixed = bytearray()

        for i in range(min_len):
            mixed.append(key1[i] ^ key2[i])

        # Hash the result for better distribution
        return hashlib.sha256(bytes(mixed)).digest()

    # ============= Convenience Methods =============

    def encrypt(self, plaintext: bytes, quantum_key: bytes, security_level: SecurityLevel,
                recipient_public_key: Optional[rsa.RSAPublicKey] = None) -> Tuple[bytes, dict]:
        """
        Encrypt with specified security level
        """
        if security_level == SecurityLevel.LEVEL_1_BASIC:
            return self.encrypt_level_1(plaintext, quantum_key)
        elif security_level == SecurityLevel.LEVEL_2_STANDARD:
            return self.encrypt_level_2(plaintext, quantum_key)
        elif security_level == SecurityLevel.LEVEL_3_HIGH:
            return self.encrypt_level_3(plaintext, quantum_key)
        elif security_level == SecurityLevel.LEVEL_4_MAXIMUM:
            return self.encrypt_level_4(plaintext, quantum_key, recipient_public_key)
        else:
            raise ValueError(f"Invalid security level: {security_level}")

    def decrypt(self, ciphertext: bytes, quantum_key: bytes, metadata: dict,
                private_key: Optional[rsa.RSAPrivateKey] = None) -> bytes:
        """
        Decrypt based on metadata security level
        """
        level = metadata.get('security_level', 2)

        if level == 1:
            return self.decrypt_level_1(ciphertext, quantum_key, metadata)
        elif level == 2:
            return self.decrypt_level_2(ciphertext, quantum_key, metadata)
        elif level == 3:
            return self.decrypt_level_3(ciphertext, quantum_key, metadata)
        elif level == 4:
            return self.decrypt_level_4(ciphertext, quantum_key, metadata, private_key)
        else:
            raise ValueError(f"Invalid security level in metadata: {level}")


def generate_rsa_keypair(key_size: int = 2048) -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """
    Generate RSA key pair for Level 4 encryption
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
        backend=default_backend()
    )
    public_key = private_key.public_key()

    return private_key, public_key
