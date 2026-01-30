import requests
import json
import base64
import urllib3
from typing import Tuple, Dict, Optional

# Suppress warnings for self-signed CAs (common in private QKD networks)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class QuKayDeeProvider:
    """
    Implements ETSI GS QKD 014 API calls for QuKayDee.
    Handles mutual TLS (mTLS) authentication and key parsing.
    """
    def __init__(self, host: str, cert_path: str, key_path: str, ca_path: str):
        self.host = host.rstrip("/")
        # Tuple for client authentication: (public_cert, private_key)
        self.cert = (cert_path, key_path)
        # Path to the Server CA to verify we are talking to the real KME
        self.verify = ca_path

    def request_key(self, sender_id: str, receiver_id: str, key_size_bits: int = 256) -> Tuple[str, bytes, Dict]:
        """
        Equivalent to the Sender (Alice) workflow.
        Calls: GET /api/v1/keys/{slave_sae_id}/enc_keys
        """
        # Endpoint: Request a key to share with the receiver (slave_sae_id)
        url = f"{self.host}/api/v1/keys/{receiver_id}/enc_keys"
        
        # Some implementations accept size requests, others default to configuration
        params = {"size": key_size_bits}

        try:
            print(f"📡 [QuKayDee] Requesting enc_key for peer {receiver_id}...")
            response = requests.get(
                url, 
                params=params, 
                cert=self.cert, 
                verify=self.verify
            )
            response.raise_for_status()
            
            data = response.json()
            # ETSI 014 returns a list of keys, we take the first one
            key_data = data["keys"][0]
            
            # Handle variable capitalization in API responses (key_id vs key_ID)
            key_id = key_data.get("key_id") or key_data.get("key_ID")
            key_b64 = key_data.get("key")
            
            if not key_id or not key_b64:
                raise ValueError("Response missing 'key_ID' or 'key' field")

            # Decode Base64 key to raw bytes for the crypto engine
            key_bytes = base64.b64decode(key_b64)
            
            metadata = {
                "source": "QuKayDee",
                "protocol": "ETSI_014",
                "key_size": len(key_bytes) * 8
            }
            
            print(f"✅ Key obtained: {key_id}")
            return key_id, key_bytes, metadata

        except Exception as e:
            print(f"❌ [QuKayDee] Request Failed: {e}")
            if 'response' in locals():
                print(f"Server Response: {response.text}")
            raise e

    def retrieve_key(self, sender_id: str, key_id: str) -> Tuple[bytes, Dict]:
        """
        Equivalent to the Receiver (Bob) workflow.
        Calls: GET /api/v1/keys/{master_sae_id}/dec_keys
        """
        # Endpoint: Retrieve a specific key created by the sender (master_sae_id)
        url = f"{self.host}/api/v1/keys/{sender_id}/dec_keys"
        
        # Try lowercase 'key_id' first (standard compliant)
        params = {"key_id": key_id}

        try:
            print(f"📡 [QuKayDee] Fetching dec_key {key_id} from {sender_id}...")
            response = requests.get(
                url, 
                params=params, 
                cert=self.cert, 
                verify=self.verify
            )
            
            # If 404, retry with 'key_ID' (some implementations differ)
            if response.status_code == 404:
                 print("   (404 on 'key_id', retrying with 'key_ID'...)")
                 response = requests.get(
                     url, 
                     params={"key_ID": key_id}, 
                     cert=self.cert, 
                     verify=self.verify
                 )
            
            response.raise_for_status()
            
            data = response.json()
            key_data = data["keys"][0]
            
            key_b64 = key_data.get("key")
            key_bytes = base64.b64decode(key_b64)
            
            metadata = {
                "source": "QuKayDee",
                "protocol": "ETSI_014",
                "key_size": len(key_bytes) * 8
            }
            
            print(f"✅ Key retrieved successfully.")
            return key_bytes, metadata

        except Exception as e:
            print(f"❌ [QuKayDee] Retrieve Failed: {e}")
            if 'response' in locals():
                print(f"Server Response: {response.text}")
            raise e