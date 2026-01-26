from typing import Tuple, Dict
from src.qkd.provider import QKDProvider
from src.qkd.qkd_simulator import QKDChannel


class LocalQKDProvider(QKDProvider):
    """
    Local BB84-based QKD provider.
    ETSI-compatible with QuKayDeeProvider.
    """

    def __init__(self, key_length: int = 256):
        self.channel = QKDChannel(key_length=key_length)

    def request_key(
        self,
        sender_id: str,
        receiver_id: str,
        key_size_bits: int = 256,   # ✅ FIX: match ETSI naming
    ) -> Tuple[str, bytes, Dict]:
        """
        ETSI-compatible:
        returns (key_id, key_bytes, metadata)
        """

        quantum_key, key_id = self.channel.establish_key_pair(
            sender_id,
            receiver_id,
            key_length=key_size_bits,
        )

        return key_id, quantum_key, {
            "expires_in": 600,
            "source": "local-bb84",
            "standard": "TEST",
        }

    def retrieve_key(
        self,
        sender_id: str,
        key_id: str,
    ) -> Tuple[bytes, Dict]:
        """
        ETSI dec_keys equivalent.
        """

        key = self.channel.get_key(key_id)

        return key, {
            "source": "local-bb84",
            "standard": "TEST",
        }