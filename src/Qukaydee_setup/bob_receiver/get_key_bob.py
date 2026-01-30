import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
API_HOST = "https://kme-2.acct-3000.etsi-qkd-api.qukaydee.com"
MY_SAE_ID = "sae-2"   # Bob
PEER_SAE_ID = "sae-1" # Alice

# Bob's Certificates (Ensure these exist!)
CERT_FILE = "sae-2.crt"
KEY_FILE = "sae-2.key"
CA_FILE = "../certs/account-3000-server-ca-qukaydee-com.crt"

def get_key_by_id(key_id):
    # Bob requests the specific key Alice created
    url = f"{API_HOST}/api/v1/keys/{PEER_SAE_ID}/dec_keys"
    params = {'key_ID': key_id}
    
    print(f"Fetching key for ID: {key_id}...")
    
    try:
        response = requests.get(
            url,
            params=params,
            cert=(CERT_FILE, KEY_FILE),
            verify=CA_FILE
        )
        
        if response.status_code == 200:
            data = response.json()
            key_value = data['keys'][0]['key']
            
            print(f"\nSUCCESS! Key retrieved for {MY_SAE_ID}")
            print(f"Key ID: {key_id}")
            print(f"Key:    {key_value}")
        else:
            print(f"\nError: {response.status_code}")
            print(f"Message: {response.text}")

    except Exception as e:
        print(f"\nConnection failed: {e}")

if __name__ == "__main__":
    target_id = input("Enter the Key ID provided by Alice: ")
    get_key_by_id(target_id)
