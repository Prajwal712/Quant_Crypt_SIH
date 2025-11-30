# Quantum Email Encryption - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
```bash
# Python 3.8 or higher
python --version

# Pip package manager
pip --version
```

### Step 1: Install Dependencies

```bash
cd Quant_Crypt_SIH
pip install -r requirements.txt
```

### Step 2: Run Examples

#### Option A: Run All Examples
```bash
cd examples
python example_usage.py
```

This will demonstrate all 4 security levels:
- Level 1: XOR encryption
- Level 2: AES-256-GCM
- Level 3: ChaCha20-Poly1305
- Level 4: Hybrid RSA+AES+Quantum

#### Option B: Launch GUI Application
```bash
cd src/GUI
python quantum_email_gui.py
```

**GUI Usage**:
1. Click "Initialize System" in Setup tab
2. Go to "Send Email" tab
3. Fill in email details
4. Select security level
5. Click "Send Encrypted Email"

### Step 3: Test Individual Components

#### Test QKD Module
```python
from src.qkd.qkd_simulator import QKDChannel

# Create QKD channel
qkd = QKDChannel(key_length=256)

# Generate quantum key
quantum_key, key_id = qkd.establish_key_pair("alice", "bob")

print(f"Generated quantum key: {key_id}")
print(f"Key length: {len(quantum_key)} bytes")
```

#### Test Encryption
```python
from src.cryptography.security_levels import EncryptionEngine, SecurityLevel
from src.qkd.qkd_simulator import QKDChannel

# Setup
qkd = QKDChannel()
engine = EncryptionEngine()
key, key_id = qkd.establish_key_pair("alice", "bob")

# Encrypt
message = b"Secret message!"
ciphertext, metadata = engine.encrypt(
    message,
    key,
    SecurityLevel.LEVEL_2_STANDARD
)

# Decrypt
plaintext = engine.decrypt(ciphertext, key, metadata)
print(f"Decrypted: {plaintext.decode()}")
```

#### Test Key Management
```python
from src.key_management.key_manager import KeyManager
from src.qkd.qkd_simulator import QKDChannel

# Create managers
alice = KeyManager("alice")
qkd = QKDChannel()

# Generate and store key
key, key_id = qkd.establish_key_pair("alice", "bob")
alice.store_key(key, key_id, {"purpose": "test"})

# Retrieve key
retrieved = alice.get_key(key_id)
print(f"Retrieved key: {retrieved.hex()[:32]}...")
```

## 🔐 Security Levels Guide

### When to Use Each Level

| Level | Use Case | Example |
|-------|----------|---------|
| 1 | Maximum speed needed | Real-time chat, IoT sensors |
| 2 | General secure email | Business communication |
| 3 | High-security needs | Financial data, legal documents |
| 4 | Critical data | Government, military, trade secrets |

### Quick Comparison

```
Level 1: ⚡⚡⚡⚡⚡ Speed  🔒🔒🔒 Security
Level 2: ⚡⚡⚡⚡   Speed  🔒🔒🔒🔒 Security
Level 3: ⚡⚡⚡     Speed  🔒🔒🔒🔒🔒 Security
Level 4: ⚡⚡       Speed  🔒🔒🔒🔒🔒🔒 Security
```

## 📧 Gmail Integration (Optional)

### Setup Gmail API

1. **Create Google Cloud Project**
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project
   - Enable Gmail API

2. **Create Credentials**
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Select "Desktop App"
   - Download `credentials.json`

3. **Place Credentials**
   ```bash
   mv ~/Downloads/credentials.json src/email_engine/credentials.json
   ```

4. **First Run**
   ```python
   from src.email_engine.auth import get_gmail_service

   # This will open browser for authentication
   service = get_gmail_service()
   ```

## 🌐 REST API (Optional)

### Start API Server
```python
from src.key_management.api import KeyManagementAPI
from src.key_management.key_manager import KeyManager
from src.qkd.qkd_simulator import QKDChannel

qkd = QKDChannel()
manager = KeyManager("api_manager")
api = KeyManagementAPI(manager, qkd)

# Start server
api.run(host='localhost', port=5000)
```

### Test API
```bash
# In another terminal
cd examples
python rest_api_example.py
```

## 💡 Common Tasks

### Send Encrypted Email (Programmatic)
```python
from src.email_engine.quantum_email import QuantumEmailEngine
from src.email_engine.auth import get_gmail_service
from src.cryptography.security_levels import SecurityLevel
from src.qkd.qkd_simulator import QKDChannel
from src.key_management.key_manager import KeyManager

# Setup
gmail = get_gmail_service()
qkd = QKDChannel()
alice = KeyManager("alice")
bob = KeyManager("bob")
engine = QuantumEmailEngine(gmail, alice, qkd, EncryptionEngine())

# Send
result = engine.send_encrypted_email(
    sender="your@email.com",
    recipient="recipient@email.com",
    subject="Test",
    plaintext_content="Hello, quantum world!",
    security_level=SecurityLevel.LEVEL_2_STANDARD,
    recipient_key_manager=bob
)

print(f"Sent! Message ID: {result['message_id']}")
```

### Generate Keys for Multiple Users
```python
from src.key_management.key_manager import KeyManager, KeyExchangeProtocol
from src.qkd.qkd_simulator import QKDChannel

qkd = QKDChannel()
exchange = KeyExchangeProtocol(qkd)

# Create managers for multiple users
users = {
    "alice": KeyManager("alice"),
    "bob": KeyManager("bob"),
    "charlie": KeyManager("charlie")
}

# Generate keys between Alice and Bob
key_id, key = exchange.request_key(users["alice"], users["bob"])
print(f"Alice ↔ Bob: {key_id}")

# Generate keys between Alice and Charlie
key_id, key = exchange.request_key(users["alice"], users["charlie"])
print(f"Alice ↔ Charlie: {key_id}")
```

## 🐛 Troubleshooting

### Import Errors
```bash
# Add project to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/Quant_Crypt_SIH"

# Or in Windows
set PYTHONPATH=%PYTHONPATH%;C:\path\to\Quant_Crypt_SIH
```

### Gmail Authentication Issues
```bash
# Delete token and re-authenticate
rm src/email_engine/token.json
python -c "from src.email_engine.auth import get_gmail_service; get_gmail_service()"
```

### Key Not Found
```python
# Check if key exists and hasn't expired
manager.list_keys()

# Cleanup expired keys
manager.cleanup_expired_keys()
```

## 📚 Next Steps

1. **Read Full Documentation**: See [DOCUMENTATION.md](DOCUMENTATION.md)
2. **Understand Security Levels**: Review security level details
3. **Explore Examples**: Check `examples/` directory
4. **Customize**: Modify security parameters for your use case
5. **Deploy**: Set up for production with real QKD hardware

## 🔗 Resources

- [README.md](README.md) - Project overview
- [DOCUMENTATION.md](DOCUMENTATION.md) - Technical details
- [examples/](examples/) - Code examples
- [src/](src/) - Source code

## ❓ Support

For questions or issues:
1. Check [DOCUMENTATION.md](DOCUMENTATION.md)
2. Review examples in `examples/`
3. Open GitHub issue

---

**Happy Quantum Encrypting! 🔐**
