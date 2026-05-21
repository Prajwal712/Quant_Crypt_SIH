import os
import shutil
from src.key_management.api import KeyManagementAPI
from src.key_management.key_manager import KeyManager
from src.qkd.qkd_simulator import QKDChannel


def test_register_user():
    # Setup
    admin_km = KeyManager(manager_id="admin")
    qkd = QKDChannel()
    api = KeyManagementAPI(admin_km, qkd)
    client = api.app.test_client()

    username = "testuser"

    # Clean up before
    target_dir = os.path.join('src', 'Qukaydee_setup', username)
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    # Call registration
    resp = client.post('/api/v1/users/register', json={'username': username})

    assert resp.status_code == 201, f"Unexpected status: {resp.status_code} - {resp.data}"

    data = resp.get_json()
    assert data['username'] == username
    assert os.path.exists(data['cert'])
    assert os.path.exists(data['key'])

    print('Registration test passed.')

    # Cleanup
    try:
        shutil.rmtree(target_dir)
        if os.path.exists('client-root-ca.key'):
            os.remove('client-root-ca.key')
        if os.path.exists('client-root-ca.crt'):
            os.remove('client-root-ca.crt')
        users_file = os.path.join('src', 'key_management', 'users.json')
        if os.path.exists(users_file):
            os.remove(users_file)
    except Exception:
        pass


if __name__ == '__main__':
    test_register_user()