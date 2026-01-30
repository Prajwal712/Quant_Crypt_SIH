import requests
import json
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURATION ---
API_HOST = "https://kme-1.acct-3000.etsi-qkd-api.qukaydee.com"
MY_SAE_ID = "sae-1"
PEER_SAE_ID = "sae-2"

# Paths (updated to point to the correct ../certs folder)
CERT_FILE = "sae-1.crt"
KEY_FILE = "sae-1.key"
CA_FILE = "../certs/account-3000-server-ca-qukaydee-com.crt"

def get_key():
    url = f"{API_HOST}/api/v1/keys/{PEER_SAE_ID}/enc_keys"
    
    print(f"Connecting to: {url}...")

    try:
        response = requests.get(
            url,
            cert=(CERT_FILE, KEY_FILE),
            verify=CA_FILE
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # --- DEBUGGING LINE ---
            print("\n--- SERVER RESPONSE ---")
            print(json.dumps(data, indent=2))
            print("-----------------------\n")
            # ----------------------

            # We try to grab the key, but catch the specific error if the name is wrong
            try:
                # The script failed here before. 
                # Look at the print output above to see if it should be 'id' or 'keyID'
                key_id = data['keys'][0]['key_ID']
                key_value = data['keys'][0]['key']
                
                print(f"SUCCESS! Key fetched for {MY_SAE_ID}")
                print(f"Key ID: {key_id}") 
                print(f"Key:    {key_value}")
                
            except KeyError as k:
                print(f"ERROR: The script expected a field named {k}, but the server didn't send it.")
                print("Check the 'SERVER RESPONSE' above to see the correct field name.")
                
        else:
            print(f"Server Error: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    get_key()
