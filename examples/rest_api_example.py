"""
REST API Example for Key Management
Demonstrates how to run and interact with the Key Management API
"""
import sys
sys.path.append('..')

from src.qkd.qkd_simulator import QKDChannel
from src.key_management.key_manager import KeyManager
from src.key_management.api import KeyManagementAPI
import threading
import time
import requests


def run_api_server():
    """
    Run the REST API server
    """
    # Initialize components
    qkd_channel = QKDChannel(key_length=256)
    key_manager = KeyManager("api_manager_1")

    # Create API instance
    api = KeyManagementAPI(key_manager, qkd_channel)

    print("Starting Key Management API server on http://localhost:5000")
    api.run(host='localhost', port=5000, debug=False)


def test_api_client():
    """
    Test the API endpoints
    """
    base_url = "http://localhost:5000/api/v1"

    # Wait for server to start
    time.sleep(2)

    print("\n" + "=" * 60)
    print("TESTING KEY MANAGEMENT API")
    print("=" * 60 + "\n")

    # 1. Login
    print("1. Authenticating...")
    login_response = requests.post(
        f"{base_url}/auth/login",
        json={"username": "admin", "password": "password"}
    )

    if login_response.status_code == 200:
        token = login_response.json()['token']
        print(f"   ✓ Login successful, token: {token[:20]}...")
    else:
        print(f"   ✗ Login failed: {login_response.text}")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Request a new key
    print("\n2. Requesting new quantum key...")
    key_request = requests.post(
        f"{base_url}/keys/request",
        json={"peer_manager_id": "peer_manager_1", "key_length": 256},
        headers=headers
    )

    if key_request.status_code == 201:
        key_data = key_request.json()
        key_id = key_data['key_id']
        print(f"   ✓ Key generated successfully")
        print(f"   Key ID: {key_id}")
        print(f"   Quantum Key: {key_data['quantum_key'][:40]}...")
    else:
        print(f"   ✗ Key request failed: {key_request.text}")
        return

    # 3. Retrieve the key
    print(f"\n3. Retrieving key {key_id}...")
    get_response = requests.get(
        f"{base_url}/keys/{key_id}",
        headers=headers
    )

    if get_response.status_code == 200:
        print(f"   ✓ Key retrieved successfully")
        print(f"   Quantum Key: {get_response.json()['quantum_key'][:40]}...")
    else:
        print(f"   ✗ Key retrieval failed: {get_response.text}")

    # 4. List all keys
    print("\n4. Listing all keys...")
    list_response = requests.get(
        f"{base_url}/keys",
        headers=headers
    )

    if list_response.status_code == 200:
        keys = list_response.json()['keys']
        print(f"   ✓ Found {len(keys)} key(s)")
        for key_info in keys:
            print(f"   - {key_info['key_id']}")
    else:
        print(f"   ✗ List keys failed: {list_response.text}")

    # 5. Delete a key
    print(f"\n5. Deleting key {key_id}...")
    delete_response = requests.delete(
        f"{base_url}/keys/{key_id}",
        headers=headers
    )

    if delete_response.status_code == 200:
        print(f"   ✓ Key deleted successfully")
    else:
        print(f"   ✗ Key deletion failed: {delete_response.text}")

    print("\n" + "=" * 60)
    print("API TESTING COMPLETED")
    print("=" * 60 + "\n")


def main():
    """
    Main function to run API server and client tests
    """
    print("\nQuantum Key Management REST API Example\n")

    # Start API server in background thread
    server_thread = threading.Thread(target=run_api_server, daemon=True)
    server_thread.start()

    # Run client tests
    try:
        test_api_client()
    except Exception as e:
        print(f"\nError during testing: {str(e)}")

    print("\nPress Ctrl+C to stop the server...")

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == '__main__':
    main()
