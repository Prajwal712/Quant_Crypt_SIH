from cryptography.hazmat.primitives.ciphers.aead import AESGCM
def aes(key: bytes, nonce: bytes, plaintext: bytes) -> bytes:
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return ciphertext

def xor(key: bytes, data: bytes) -> bytes:
    result = bytearray()
    for i in range(len(data)):
        result.append(data[i] ^ key[i % len(key)])
    return bytes(result)

