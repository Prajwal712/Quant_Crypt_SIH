import encrypt
import decrypt
import os
import hashlib

def run_tests():
    """
    Runs a series of tests to verify encryption and decryption functions.
    """
    print("--- Starting Encryption/Decryption Verification ---")
    
    # --- Test Case 1: Standard Text ---
    message = "This is a secret message that needs to be kept safe."
    key = "a-very-secret-key-123!"
    
    # Convert strings to bytes, as required by the new functions
    message_bytes = message.encode('utf-8')
    key_bytes = key.encode('utf-8')
    
    print(f"\nOriginal Message: '{message}'")
    print(f"Secret Key: '{key}'")
    print("-" * 20)

    # --- XOR Test ---
    print("\n[TESTING XOR ENCRYPTION]")
    try:
        # 1. Encrypt the message using XOR
        xor_encrypted = encrypt.xor(key_bytes, message_bytes)
        # Printing the hex representation for readability
        print(f"XOR Encrypted (hex): {xor_encrypted.hex()}")

        # 2. Decrypt the message using XOR
        xor_decrypted_bytes = decrypt.xor(key_bytes, xor_encrypted)
        xor_decrypted = xor_decrypted_bytes.decode('utf-8')
        print(f"XOR Decrypted: '{xor_decrypted}'")
        
        # 3. Verify the result
        if message == xor_decrypted:
            print("✅ XOR TEST SUCCESS: Original and decrypted messages match.")
        else:
            print("❌ XOR TEST FAILED: Messages do not match.")
            
    except Exception as e:
        print(f"An error occurred during XOR test: {e}")

    # --- AES Test ---
    print("\n[TESTING AES-GCM ENCRYPTION]")
    try:
        # AES-GCM requires a key of a specific length (16, 24, or 32 bytes).
        # We'll use SHA-256 to hash the password into a 32-byte key.
        hashed_key = hashlib.sha256(key_bytes).digest()
        
        # AES-GCM also requires a "nonce" (number used once). A 12-byte nonce is standard.
        # This nonce must be used for both encryption and decryption.
        nonce = os.urandom(12)
        
        # 1. Encrypt the message using AES
        aes_encrypted = encrypt.aes(hashed_key, nonce, message_bytes)
        print(f"AES Encrypted (hex): {aes_encrypted.hex()}")
        
        # 2. Decrypt the message using AES
        aes_decrypted_bytes = decrypt.aes(hashed_key, nonce, aes_encrypted)
        aes_decrypted = aes_decrypted_bytes.decode('utf-8')
        print(f"AES Decrypted: '{aes_decrypted}'")
        
        # 3. Verify the result
        if message == aes_decrypted:
            print("✅ AES TEST SUCCESS: Original and decrypted messages match.")
        else:
            print("❌ AES TEST FAILED: Messages do not match.")

    except Exception as e:
        print(f"An error occurred during AES test: {e}")
        
    print("\n--- Verification Complete ---")


if __name__ == '__main__':
    run_tests()

