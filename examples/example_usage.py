"""
Example Usage: Quantum-Encrypted Email System
Demonstrates all 4 security levels
"""
import sys
sys.path.append('..')


from src.key_management.key_manager import KeyManager, KeyExchangeProtocol
from src.cryptography.security_levels import EncryptionEngine, SecurityLevel, generate_rsa_keypair



from src.qkd.local_provider import LocalQKDProvider

def example_1_basic_encryption():
    """
    Example 1: Level 1 - Basic XOR Encryption
    Fastest, suitable for low-latency applications
    """
    print("=" * 60)
    print("EXAMPLE 1: Level 1 - Basic XOR Encryption")
    print("=" * 60)

    # Initialize components
    provider = LocalQKDProvider()

    sender_manager = KeyManager("alice")
    receiver_manager = KeyManager("bob")
    encryption_engine = EncryptionEngine()

    # Generate quantum key
    key_exchange = KeyExchangeProtocol(provider)
    key_id, quantum_key = key_exchange.request_key(sender_manager, receiver_manager)

    print(f"✓ Quantum key generated: {key_id}")

    # Encrypt message
    message = "This is a secret message with Level 1 encryption!"
    ciphertext, metadata = encryption_engine.encrypt(
        message.encode('utf-8'),
        quantum_key,
        SecurityLevel.LEVEL_1_BASIC
    )

    print(f"✓ Message encrypted with {metadata['algorithm']}")
    print(f"  Ciphertext length: {len(ciphertext)} bytes")

    # Decrypt message
    retrieved = receiver_manager.get_key(key_id)
    quantum_key = retrieved["key"]

    plaintext = encryption_engine.decrypt(ciphertext, quantum_key, metadata)

    print(f"✓ Message decrypted: {plaintext.decode('utf-8')}")
    print()


def example_2_standard_encryption():
    """
    Example 2: Level 2 - Standard AES-256-GCM
    Balanced security and performance
    """
    print("=" * 60)
    print("EXAMPLE 2: Level 2 - Standard AES-256-GCM")
    print("=" * 60)

    # Initialize components
    provider = LocalQKDProvider(key_length=256)

    sender_manager = KeyManager("alice")
    receiver_manager = KeyManager("bob")
    encryption_engine = EncryptionEngine()

    # Generate quantum key
    key_exchange = KeyExchangeProtocol(provider)
    key_id, quantum_key = key_exchange.request_key(sender_manager, receiver_manager)

    print(f"✓ Quantum key generated: {key_id}")

    # Encrypt message
    message = "This message uses AES-256-GCM with quantum key!"
    ciphertext, metadata = encryption_engine.encrypt(
        message.encode('utf-8'),
        quantum_key,
        SecurityLevel.LEVEL_2_STANDARD
    )

    print(f"✓ Message encrypted with {metadata['algorithm']}")
    print(f"  Nonce: {metadata['nonce'][:16]}...")
    print(f"  Ciphertext length: {len(ciphertext)} bytes")

    # Decrypt message
    retrieved = receiver_manager.get_key(key_id)
    quantum_key = retrieved["key"]

    plaintext = encryption_engine.decrypt(ciphertext, quantum_key, metadata)


    print(f"✓ Message decrypted: {plaintext.decode('utf-8')}")
    print()


def example_3_high_security():
    """
    Example 3: Level 3 - High Security with ChaCha20-Poly1305
    Enhanced security with key mixing
    """
    print("=" * 60)
    print("EXAMPLE 3: Level 3 - ChaCha20-Poly1305 with Key Mixing")
    print("=" * 60)

    # Initialize components
    provider = LocalQKDProvider()
       
    sender_manager = KeyManager("alice")
    receiver_manager = KeyManager("bob")
    encryption_engine = EncryptionEngine()

    # Generate quantum key
    key_exchange = KeyExchangeProtocol(provider) 
    key_id, quantum_key = key_exchange.request_key(sender_manager, receiver_manager)

    print(f"✓ Quantum key generated: {key_id}")

    # Encrypt message
    message = "High security message with ChaCha20-Poly1305!"
    ciphertext, metadata = encryption_engine.encrypt(
        message.encode('utf-8'),
        quantum_key,
        SecurityLevel.LEVEL_3_HIGH
    )

    print(f"✓ Message encrypted with {metadata['algorithm']}")
    print(f"  Key mixing enabled: {metadata['key_mixing']}")
    print(f"  Ciphertext length: {len(ciphertext)} bytes")

    # Decrypt message
    retrieved = receiver_manager.get_key(key_id)
    quantum_key = retrieved["key"]

    plaintext = encryption_engine.decrypt(ciphertext, quantum_key, metadata)

    print(f"✓ Message decrypted: {plaintext.decode('utf-8')}")
    print()


def example_4_maximum_security():
    """
    Example 4: Level 4 - Maximum Security (Hybrid)
    RSA + AES-256-GCM + Quantum Key
    """
    print("=" * 60)
    print("EXAMPLE 4: Level 4 - Maximum Security (Hybrid)")
    print("=" * 60)

    # Initialize components
    provider = LocalQKDProvider()

    sender_manager = KeyManager("alice")
    receiver_manager = KeyManager("bob")
    encryption_engine = EncryptionEngine()

    # Generate RSA key pair
    private_key, public_key = generate_rsa_keypair(key_size=2048)
    print("✓ RSA key pair generated (2048 bits)")

    # Generate quantum key
    key_exchange = KeyExchangeProtocol(provider)
    key_id, quantum_key = key_exchange.request_key(sender_manager, receiver_manager)

    print(f"✓ Quantum key generated: {key_id}")

    # Encrypt message
    message = "Maximum security with hybrid encryption!"
    ciphertext, metadata = encryption_engine.encrypt(
        message.encode('utf-8'),
        quantum_key,
        SecurityLevel.LEVEL_4_MAXIMUM,
        recipient_public_key=public_key
    )

    print(f"✓ Message encrypted with {metadata['algorithm']}")
    print(f"  Quantum enhanced: {metadata['quantum_enhanced']}")
    print(f"  Ciphertext length: {len(ciphertext)} bytes")

    # Decrypt message
    retrieved = receiver_manager.get_key(key_id)
    quantum_key = retrieved["key"]

    plaintext = encryption_engine.decrypt(
        ciphertext,
        quantum_key,
        metadata,
        private_key=private_key
    )

    print(f"✓ Message decrypted: {plaintext.decode('utf-8')}")
    print()


def example_5_complete_email_flow():
    """
    Example 5: Complete Email Flow with Quantum Encryption
    Demonstrates the full sender -> receiver flow
    """
    print("=" * 60)
    print("EXAMPLE 5: Complete Email Flow (Simulated)")
    print("=" * 60)

    # Note: This example simulates the flow without actually sending emails
    # To send real emails, you need to authenticate with Gmail API

    # Initialize all components
    provider = LocalQKDProvider(key_length=256)

    sender_manager = KeyManager("alice@example.com")
    receiver_manager = KeyManager("bob@example.com")
    encryption_engine = EncryptionEngine()

    print("✓ System components initialized")

    # Simulate key exchange
    key_exchange = KeyExchangeProtocol(provider)
    key_id, quantum_key = key_exchange.request_key(sender_manager, receiver_manager)

    print(f"✓ QKD channel established, Key ID: {key_id}")

    # Prepare email content
    email_content = """
    Dear Bob,

    This email is protected by quantum encryption!

    Security Level: 2 (AES-256-GCM with Quantum Key)

    Best regards,
    Alice
    """

    # Encrypt the email
    ciphertext, metadata = encryption_engine.encrypt(
        email_content.encode('utf-8'),
        quantum_key,
        SecurityLevel.LEVEL_2_STANDARD
    )

    print(f"✓ Email encrypted")
    print(f"  Algorithm: {metadata['algorithm']}")
    print(f"  Size: {len(ciphertext)} bytes")

    # Simulate transmission...
    print("✓ Email transmitted via SMTP")

    # Receiver side: Decrypt email
    retrieved = receiver_manager.get_key(key_id)
    quantum_key = retrieved["key"]

    decrypted_content = encryption_engine.decrypt(
        ciphertext,
        quantum_key,
        metadata
    )

    print("✓ Email decrypted successfully")
    print("\nDecrypted content:")
    print("-" * 40)
    print(decrypted_content.decode('utf-8'))
    print("-" * 40)
    print()


def example_6_key_management():
    """
    Example 6: Key Management Operations
    Demonstrates key lifecycle management
    """
    print("=" * 60)
    print("EXAMPLE 6: Key Management Operations")
    print("=" * 60)

    # Initialize key manager
    manager = KeyManager("alice")
    provider = LocalQKDProvider()
    exchange = KeyExchangeProtocol(provider)

    # Generate multiple keys
    print("Generating quantum keys...")
    for i in range(3):
        key_id, quantum_key = exchange.request_key(manager, KeyManager("bob"))

        print(f"  ✓ Key {i+1}: {key_id}")

    # List all keys
    print("\nActive keys:")
    keys = manager.list_keys()
    for key_info in keys:
        print(f"  - {key_info['key_id']}")
        print(f"    Created: {key_info['created_at']}")
        print(f"    Usage: {key_info['usage_count']}")

    # Retrieve and use a key
    print("\nRetrieving key...")
    key_id = keys[0]['key_id']
    retrieved = manager.get_key(key_id)
    print(f"  ✓ Retrieved key: {key_id}")
    print(f"  Key length: {len(retrieved['key'])} bytes")

    # Cleanup
    print("\nCleaning up expired keys...")
    cleaned = manager.cleanup_expired_keys()
    print(f"  ✓ Removed {cleaned} expired keys")
    print()


def main():
    """
    Run all examples
    """
    print("\n")
    print("*" * 60)
    print("QUANTUM-ENCRYPTED EMAIL SYSTEM - EXAMPLES")
    print("*" * 60)
    print("\n")

    # Run examples
    example_1_basic_encryption()
    example_2_standard_encryption()
    example_3_high_security()
    example_4_maximum_security()
    example_5_complete_email_flow()
    example_6_key_management()

    print("=" * 60)
    print("ALL EXAMPLES COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == '__main__':
    main()
