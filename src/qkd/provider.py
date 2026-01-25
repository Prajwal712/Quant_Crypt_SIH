from abc import ABC, abstractmethod
from typing import Tuple

class QKDProvider(ABC):

    @abstractmethod
    def request_key(
        self,
        sender_id: str,
        receiver_id: str,
        key_size: int = 256
    ) -> Tuple[str, bytes]:
        """
        Returns (key_id, key_bytes)
        """
        pass