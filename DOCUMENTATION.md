# Quantum Email Encryption System - Technical Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Security Levels](#security-levels)
4. [Quantum Key Distribution](#quantum-key-distribution)
5. [Key Management](#key-management)
6. [Cryptography Implementation](#cryptography-implementation)
7. [Email Engine](#email-engine)
8. [REST API](#rest-api)
9. [GUI Application](#gui-application)
10. [Security Considerations](#security-considerations)

---

## System Overview

The Quantum Email Encryption System is a comprehensive solution for secure email communication using quantum-enhanced cryptography. It combines traditional encryption methods with Quantum Key Distribution (QKD) to provide multiple levels of security.

### Key Components

1. **QKD Module**: Simulates BB84 quantum key distribution protocol
2. **Key Management**: Handles quantum key lifecycle and storage
3. **Cryptography Engine**: Provides 4 security levels
4. **Email Engine**: Integrates with Gmail for sending/receiving
5. **REST API**: Remote key management operations
6. **GUI Application**: User-friendly interface

---

## Architecture

### System Flow

```
┌─────────────┐
│   Sender    │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────┐
│  1. Request Quantum Key (QKD)   │
└──────┬──────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│  2. Encrypt Email Content       │
│     (Selected Security Level)   │
└──────┬──────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│  3. Package Encrypted Data      │
│     with Key ID & Metadata      │
└──────┬──────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│  4. Send via SMTP (Gmail)       │
└─────────────────────────────────┘
       │
       │  Email Transmission
       │
       ↓
┌─────────────────────────────────┐
│  5. Receive via IMAP (Gmail)    │
└──────┬──────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│  6. Extract Encrypted Package   │
└──────┬──────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│  7. Retrieve Quantum Key        │
│     (using Key ID)              │
└──────┬──────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│  8. Decrypt Email Content       │
└──────┬──────────────────────────┘
       │
       ↓
┌──────────────┐
│   Receiver   │
└──────────────┘
```

---

## Security Levels

### Level 1: Basic (XOR with Quantum Key)

**Algorithm**: One-Time Pad (OTP) using XOR operation

**Characteristics**:
- Information-theoretically secure when used correctly
- Fastest encryption/decryption
- Key must be at least as long as plaintext
- Key is never reused (enforced by key management)

**Implementation**:
```python
ciphertext[i] = plaintext[i] XOR quantum_key[i % key_length]
```

**Use Cases**:
- High-volume, low-latency communications
- Trusted quantum key infrastructure
- Short messages

**Security Notes**:
- Provides perfect secrecy if:
  - Key is truly random (quantum-generated)
  - Key is used only once
  - Key is secret

---

### Level 2: Standard (AES-256-GCM)

**Algorithm**: AES-256 in Galois/Counter Mode

**Characteristics**:
- Industry-standard authenticated encryption
- Fast hardware acceleration available
- 256-bit key derived from quantum key
- 96-bit random nonce
- Built-in authentication tag

**Implementation**:
```python
key = HKDF(quantum_key, 32 bytes)
nonce = random(12 bytes)
ciphertext = AES-GCM-Encrypt(key, nonce, plaintext)
```

**Use Cases**:
- General secure communications
- Large messages
- Standard compliance requirements

**Security Notes**:
- NIST-approved algorithm
- Resistant to chosen-plaintext attacks
- Provides confidentiality and authenticity
- Quantum key adds entropy

---

### Level 3: High (ChaCha20-Poly1305)

**Algorithm**: ChaCha20 stream cipher with Poly1305 MAC

**Characteristics**:
- Enhanced security through key mixing
- Resistant to timing attacks
- No hardware requirements
- 256-bit mixed key
- 96-bit random nonce

**Implementation**:
```python
entropy = random(32 bytes)
mixed_key = quantum_key XOR entropy
final_key = SHA256(mixed_key)
nonce = random(12 bytes)
ciphertext = ChaCha20-Poly1305-Encrypt(final_key, nonce, plaintext)
```

**Use Cases**:
- High-security requirements
- Environments without AES acceleration
- Additional entropy mixing desired

**Security Notes**:
- Designed by Daniel J. Bernstein
- Used in TLS, SSH, and VPNs
- Constant-time implementation
- Key mixing provides defense in depth

---

### Level 4: Maximum (Hybrid RSA+AES+Quantum)

**Algorithm**: Hybrid cryptosystem combining RSA, AES-256-GCM, and Quantum Key

**Characteristics**:
- Multi-layered security
- Post-quantum resistance preparation
- Ephemeral key encryption
- 2048-bit RSA (configurable to 4096)
- Combined quantum and classical security

**Implementation**:
```python
ephemeral_key = random(32 bytes)
final_key = ephemeral_key XOR quantum_key
encrypted_ephemeral = RSA-Encrypt(recipient_public_key, ephemeral_key)
nonce = random(12 bytes)
ciphertext = AES-GCM-Encrypt(final_key, nonce, plaintext)
package = {ciphertext, encrypted_ephemeral, nonce}
```

**Use Cases**:
- Maximum security requirements
- Defense in depth strategy
- Preparation for post-quantum threats
- High-value communications

**Security Notes**:
- Redundant security layers
- If RSA is broken, quantum key still protects
- If quantum channel is compromised, RSA protects
- Future-proof against quantum computers (with quantum key)

---

## Quantum Key Distribution

### BB84 Protocol Implementation

The system implements a simulation of the BB84 quantum key distribution protocol.

#### Steps:

1. **Preparation Phase**
   ```python
   alice_bits = random_bits(length)
   alice_bases = random_bases(length)  # RECTILINEAR or DIAGONAL
   ```

2. **Transmission Phase**
   ```python
   # Simulate quantum channel
   for each qubit:
       alice encodes bit in chosen basis
       bob measures in random basis
   ```

3. **Basis Reconciliation (Sifting)**
   ```python
   # Public communication of bases (not bits)
   for each position:
       if alice_basis == bob_basis:
           keep this bit (sifted key)
       else:
           discard this bit
   ```

4. **Error Estimation**
   ```python
   # Sample random positions
   QBER = count_errors / sample_size
   if QBER > threshold (default 11%):
       abort - possible eavesdropping
   ```

5. **Privacy Amplification**
   ```python
   # Compress key to remove potential information leakage
   final_key = SHA256(sifted_bits)
   ```

#### Security Parameters

- **Key Length**: 256 bits (configurable)
- **QBER Threshold**: 11% (standard for BB84)
- **Transmission Length**: 4× desired key length
- **Sample Size for Error Estimation**: 50 bits (configurable)

---

## Key Management

### Key Lifecycle

```
┌──────────────┐
│  GENERATED   │ ← QKD Protocol
└──────┬───────┘
       │
       ↓
┌──────────────┐
│    STORED    │ ← KeyManager.store_key()
└──────┬───────┘
       │
       ↓
┌──────────────┐
│    ACTIVE    │ ← Available for use
└──────┬───────┘
       │
       ├─→ USED (usage_count incremented)
       │
       ├─→ EXPIRED (24 hours)
       │
       └─→ MAX_USAGE_REACHED
           │
           ↓
       ┌──────────────┐
       │   DELETED    │ ← Secure deletion
       └──────────────┘
```

### Key Storage Format

```json
{
  "key": "hex_encoded_quantum_key",
  "key_id": "unique_identifier",
  "created_at": "2024-11-30T10:00:00",
  "expires_at": "2024-12-01T10:00:00",
  "usage_count": 0,
  "max_usage": 1,
  "metadata": {
    "peer": "bob@example.com",
    "purpose": "email_encryption",
    "key_length": 256
  }
}
```

### Key Manager API

```python
# Store a key
key_manager.store_key(quantum_key, key_id, metadata)

# Retrieve a key (auto-increments usage)
quantum_key = key_manager.get_key(key_id)

# List active keys
keys = key_manager.list_keys()

# Delete a key
key_manager.delete_key(key_id)

# Cleanup expired keys
count = key_manager.cleanup_expired_keys()
```

---

## Cryptography Implementation

### Encryption Engine

The `EncryptionEngine` class provides a unified interface for all security levels.

#### Encryption

```python
engine = EncryptionEngine()

ciphertext, metadata = engine.encrypt(
    plaintext=b"secret message",
    quantum_key=quantum_key,
    security_level=SecurityLevel.LEVEL_2_STANDARD,
    recipient_public_key=None  # Optional for Level 4
)
```

#### Decryption

```python
plaintext = engine.decrypt(
    ciphertext=ciphertext,
    quantum_key=quantum_key,
    metadata=metadata,
    private_key=None  # Optional for Level 4
)
```

### Metadata Format

```python
{
    'security_level': 2,
    'algorithm': 'AES-256-GCM',
    'nonce': 'hex_encoded_nonce',
    'key_mixing': False,
    'encrypted_key': None,  # Only for Level 4
    'quantum_enhanced': True
}
```

---

## Email Engine

### QuantumEmailEngine

Integrates all components for quantum-encrypted email.

#### Sending

```python
result = quantum_email_engine.send_encrypted_email(
    sender="alice@example.com",
    recipient="bob@example.com",
    subject="Secret Message",
    plaintext_content="This is secret!",
    security_level=SecurityLevel.LEVEL_2_STANDARD,
    recipient_key_manager=bob_key_manager,
    recipient_public_key=None
)
```

**Process**:
1. Request quantum key via QKD
2. Encrypt content with selected security level
3. Create encrypted package (JSON)
4. Send via Gmail API (SMTP)

#### Receiving

```python
result = quantum_email_engine.receive_encrypted_email(
    message_id=message_id,
    receiver_key_manager=bob_key_manager,
    private_key=None
)
```

**Process**:
1. Fetch email via Gmail API (IMAP)
2. Extract encrypted package
3. Retrieve quantum key using key_id
4. Decrypt content
5. Return plaintext and metadata

### Email Package Format

```
Subject: [QUANTUM-ENCRYPTED] Original Subject

Body:
This is a quantum-encrypted email. Use the quantum email client to decrypt.

=== ENCRYPTED PACKAGE ===
{
  "ciphertext": "base64_encoded_ciphertext",
  "key_id": "unique_key_identifier",
  "metadata": {
    "security_level": 2,
    "algorithm": "AES-256-GCM",
    "nonce": "hex_nonce"
  },
  "sender_id": "alice@example.com",
  "version": "1.0"
}
```

---

## REST API

### Authentication

All API endpoints (except login) require authentication.

```python
# Login
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "password"
}

Response:
{
  "token": "auth_token",
  "manager_id": "manager_1"
}
```

### Endpoints

#### Request New Key

```python
POST /api/v1/keys/request
Headers: Authorization: Bearer <token>
{
  "peer_manager_id": "bob",
  "key_length": 256,
  "purpose": "email_encryption"
}

Response:
{
  "key_id": "key_identifier",
  "quantum_key": "hex_encoded_key",
  "metadata": {...}
}
```

#### Get Key

```python
GET /api/v1/keys/<key_id>
Headers: Authorization: Bearer <token>

Response:
{
  "key_id": "key_identifier",
  "quantum_key": "hex_encoded_key"
}
```

#### List Keys

```python
GET /api/v1/keys
Headers: Authorization: Bearer <token>

Response:
{
  "keys": [
    {
      "key_id": "...",
      "created_at": "...",
      "expires_at": "...",
      "usage_count": 0,
      "metadata": {...}
    }
  ]
}
```

#### Delete Key

```python
DELETE /api/v1/keys/<key_id>
Headers: Authorization: Bearer <token>

Response:
{
  "message": "Key deleted successfully"
}
```

---

## GUI Application

### Main Window

The GUI is organized into 4 tabs:

1. **Setup Tab**: Initialize system components
2. **Send Email Tab**: Compose and send encrypted emails
3. **Receive Email Tab**: Fetch and decrypt emails
4. **Key Management Tab**: Manage quantum keys

### Usage Flow

1. Launch application: `python src/GUI/quantum_email_gui.py`
2. Setup Tab: Enter manager IDs and click "Initialize System"
3. Send Email Tab:
   - Enter sender/recipient emails
   - Write subject and content
   - Select security level
   - Click "Send Encrypted Email"
4. Receive Email Tab:
   - Click "Fetch Latest Email"
   - Click "Decrypt Email"
   - View decrypted content
5. Key Management Tab:
   - Generate new keys
   - List active keys
   - Cleanup expired keys

---

## Security Considerations

### Threat Model

**Protected Against**:
- Passive eavesdropping (quantum and classical)
- Man-in-the-middle attacks (with authenticated QKD)
- Key reuse attacks (enforced one-time use)
- Timing attacks (constant-time operations)

**Assumptions**:
- Secure QKD channel establishment
- Authenticated classical communication
- Secure key storage on endpoints
- Trusted computing environment

### Best Practices

1. **Key Management**:
   - Never reuse quantum keys
   - Rotate keys regularly
   - Secure deletion after use
   - Monitor QBER for anomalies

2. **Operational Security**:
   - Use Level 3 or 4 for sensitive data
   - Authenticate QKD channel participants
   - Secure API tokens properly
   - Regular security audits

3. **Implementation**:
   - Use hardware random number generators
   - Implement secure key storage (HSM in production)
   - Regular security updates
   - Penetration testing

### Limitations

1. **Simulation**: This is a BB84 simulation, not real quantum hardware
2. **Authentication**: Current implementation uses simple token auth
3. **Storage**: Keys stored on disk (should use HSM in production)
4. **Network**: Assumes secure classical channels for basis reconciliation

### Future Security Enhancements

1. Integration with real QKD hardware
2. Post-quantum cryptography (CRYSTALS-Kyber, Dilithium)
3. Hardware security module (HSM) integration
4. Zero-knowledge proofs for authentication
5. Blockchain-based audit trail
6. Multi-factor authentication
7. End-to-end verification protocols

---

## Performance Characteristics

### Encryption Speed (relative)

| Level | Algorithm | Speed | Key Generation |
|-------|-----------|-------|----------------|
| 1 | XOR-OTP | 1.0× (fastest) | ~0.5s |
| 2 | AES-256-GCM | 0.9× | ~0.5s |
| 3 | ChaCha20 | 0.8× | ~0.6s |
| 4 | Hybrid | 0.3× | ~1.0s |

### Recommended Usage

- **Level 1**: < 1 KB messages, high-frequency
- **Level 2**: < 10 MB messages, general use
- **Level 3**: < 100 MB messages, high security
- **Level 4**: Any size, maximum security

---

## Troubleshooting

### Common Issues

1. **Key Not Found**: Check key expiration and usage count
2. **QBER Too High**: Indicates potential eavesdropping or channel noise
3. **Authentication Failed**: Verify API token or Gmail credentials
4. **Decryption Error**: Ensure correct key and matching security level

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## References

1. Bennett & Brassard (1984) - BB84 Protocol
2. NIST SP 800-38D - AES-GCM Specification
3. RFC 8439 - ChaCha20-Poly1305 AEAD
4. ETSI GS QKD 014 - QKD REST API
5. RFC 7539 - ChaCha20 and Poly1305

---

**Document Version**: 1.0
**Last Updated**: 2024-11-30
**Maintained By**: SIH 2024 Team
