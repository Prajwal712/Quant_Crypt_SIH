from src.qkd.provider import QKDProvider
from src.qkd.qkd_simulator import QKDChannel

class LocalQKDProvider(QKDProvider):

    def __init__(self, key_length: int = 256):
        self.channel = QKDChannel(key_length=key_length)

    def request_key(
        self,
        sender_id: str,
        receiver_id: str,
        key_length: int = 256
    ):
        quantum_key, key_id = self.channel.establish_key_pair(
            sender_id,
            receiver_id,
            key_length=key_length
        )
        return key_id, quantum_key