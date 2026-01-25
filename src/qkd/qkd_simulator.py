"""
Quantum Key Distribution (QKD) Simulator
Simulates BB84 protocol for quantum key generation
"""
import secrets
import hashlib
from typing import Tuple, List
from enum import Enum

class Basis(Enum):
    RECTILINEAR = 0  # + basis (0°, 90°)
    DIAGONAL = 1     # × basis (45°, 135°)

class QKDSimulator:
    def __init__(self, key_length: int = 256):
        self.key_length = key_length

    def generate_random_bits(self, length: int) -> List[int]:
        return [secrets.randbelow(2) for _ in range(length)]

    def generate_random_bases(self, length: int) -> List[Basis]:
        return [Basis(secrets.randbelow(2)) for _ in range(length)]

    def simulate_quantum_channel(self, bits: List[int], bases: List[Basis],
                                 error_rate: float = 0.0) -> Tuple[List[int], List[Basis]]:
        """
        Simulate quantum channel transmission with optional errors
        In real QKD, this would be photon transmission
        """
        received_bits = []
        receiver_bases = self.generate_random_bases(len(bits))

        for i, (bit, alice_basis) in enumerate(zip(bits, bases)):
            bob_basis = receiver_bases[i]

            # If bases match, bit is correctly received (with some error rate)
            if alice_basis == bob_basis:
                if secrets.randbelow(100) < int(error_rate * 100):
                    received_bits.append(1 - bit)  # Flip bit (error)
                else:
                    received_bits.append(bit)
            else:
                # Bases don't match, random result
                received_bits.append(secrets.randbelow(2))

        return received_bits, receiver_bases

    def sift_key(self, alice_bits: List[int], alice_bases: List[Basis],
                 bob_bits: List[int], bob_bases: List[Basis]) -> Tuple[List[int], List[int]]:
        """
        Sift the key by comparing bases (basis reconciliation)
        """
        alice_sifted = []
        bob_sifted = []

        for i in range(len(alice_bases)):
            if alice_bases[i] == bob_bases[i]:
                alice_sifted.append(alice_bits[i])
                bob_sifted.append(bob_bits[i])

        return alice_sifted, bob_sifted

    def estimate_error_rate(self, alice_sifted: List[int], bob_sifted: List[int],
                           sample_size: int = 50) -> float:
        """
        Estimate the quantum bit error rate (QBER)
        """
        if len(alice_sifted) < sample_size:
            sample_size = len(alice_sifted) // 2

        errors = sum(1 for i in range(sample_size) if alice_sifted[i] != bob_sifted[i])
        return errors / sample_size if sample_size > 0 else 0.0

    def privacy_amplification(self, key_bits: List[int]) -> bytes:
        """
        Apply privacy amplification using hash function
        Reduces key to desired length while removing potential information leakage
        """
        # Convert bits to bytes
        bit_string = ''.join(map(str, key_bits))

        # Apply SHA-256 for privacy amplification
        hash_obj = hashlib.sha256(bit_string.encode())

        # For different key lengths, chain multiple hashes
        final_key = hash_obj.digest()

        if self.key_length > 256:
            # For longer keys, use multiple hash rounds
            additional_bytes = (self.key_length - 256) // 8
            for _ in range(additional_bytes // 32 + 1):
                hash_obj = hashlib.sha256(final_key)
                final_key += hash_obj.digest()

        return final_key[:self.key_length // 8]

    def generate_quantum_key(self, error_threshold: float = 0.11) -> Tuple[bytes, str]:
        """
        Complete BB84 QKD protocol simulation
        Returns: (quantum_key, key_id)
        """
        # Transmission length needs to be longer than desired key
        transmission_length = self.key_length * 4

        # Alice prepares random bits and bases
        alice_bits = self.generate_random_bits(transmission_length)
        alice_bases = self.generate_random_bases(transmission_length)

        # Simulate quantum channel transmission
        bob_bits, bob_bases = self.simulate_quantum_channel(alice_bits, alice_bases)

        # Basis reconciliation (sifting)
        alice_sifted, bob_sifted = self.sift_key(alice_bits, alice_bases,
                                                   bob_bits, bob_bases)

        # Error estimation
        error_rate = self.estimate_error_rate(alice_sifted, bob_sifted)

        if error_rate > error_threshold:
            raise Exception(f"QBER too high: {error_rate:.2%} > {error_threshold:.2%}. Possible eavesdropping!")

        # Privacy amplification to get final key
        quantum_key = self.privacy_amplification(alice_sifted)

        # Generate unique key ID
        key_id = hashlib.sha256(quantum_key).hexdigest()[:16]

        return quantum_key, key_id

class QKDChannel:
    """
    Simulates a QKD channel between two Key Managers
    """
    def __init__(self, key_length: int = 256):
        self.qkd_simulator = QKDSimulator(key_length)
        self.key_store = {}

    def establish_key_pair(
        self,
        manager_a_id: str,
        manager_b_id: str,
        key_length: int = None
    ) -> Tuple[bytes, str]:
        """
        Establish a quantum key pair between two managers.
        Supports variable key lengths (ETSI / provider-compatible).
        """

        if key_length is not None:
            # Temporarily override simulator key length
            original_length = self.qkd_simulator.key_length
            self.qkd_simulator.key_length = key_length

        quantum_key, key_id = self.qkd_simulator.generate_quantum_key()

        if key_length is not None:
            # Restore original length
            self.qkd_simulator.key_length = original_length

        self.key_store[key_id] = {
            "key": quantum_key,
            "manager_a": manager_a_id,
            "manager_b": manager_b_id
        }

        return quantum_key, key_id

    def get_key(self, key_id: str) -> bytes:
        """
        Retrieve a quantum key by ID
        """
        if key_id not in self.key_store:
            raise ValueError(f"Key ID {key_id} not found")
        return self.key_store[key_id]['key']
