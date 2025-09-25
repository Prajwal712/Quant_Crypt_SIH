from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def aes(key: bytes, nonce: bytes, ciphertext: bytes) -> bytes:
    aesgcm = AESGCM(key)
    decrypted_text = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted_text

def xor(key: bytes, data: bytes) -> bytes:
    result = bytearray()
    for i in range(len(data)):
        result.append(data[i] ^ key[i % len(key)])
    return bytes(result)
