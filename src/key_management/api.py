"""
REST API for Key Management
Provides authenticated endpoints for key operations
"""
from flask import Flask, request, jsonify
from functools import wraps
import secrets
import hashlib
from typing import Dict
from .key_manager import KeyManager
from ..qkd.qkd_simulator import QKDChannel

class KeyManagementAPI:
    def __init__(self, key_manager: KeyManager, qkd_channel: QKDChannel):
        self.app = Flask(__name__)
        self.key_manager = key_manager
        self.qkd_channel = qkd_channel

        # Simple authentication tokens (in production, use OAuth/JWT)
        self.auth_tokens: Dict[str, str] = {}

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """
        Register all API endpoints
        """
        self.app.route('/api/v1/auth/login', methods=['POST'])(self.login)
        self.app.route('/api/v1/keys/request', methods=['POST'])(self.require_auth(self.request_key))
        self.app.route('/api/v1/keys/<key_id>', methods=['GET'])(self.require_auth(self.get_key))
        self.app.route('/api/v1/keys', methods=['GET'])(self.require_auth(self.list_keys))
        self.app.route('/api/v1/keys/<key_id>', methods=['DELETE'])(self.require_auth(self.delete_key))

    def require_auth(self, f):
        """
        Authentication decorator
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            auth_header = request.headers.get('Authorization')

            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'Missing or invalid authorization header'}), 401

            token = auth_header.split(' ')[1]

            if token not in self.auth_tokens:
                return jsonify({'error': 'Invalid authentication token'}), 401

            return f(*args, **kwargs)

        return decorated_function

    def login(self):
        """
        Authenticate and receive a token
        """
        data = request.get_json()

        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Missing credentials'}), 400

        # Simple authentication (in production, verify against secure database)
        username = data['username']
        password = data['password']

        # Generate auth token
        token = secrets.token_urlsafe(32)
        self.auth_tokens[token] = username

        return jsonify({
            'token': token,
            'manager_id': self.key_manager.manager_id
        }), 200

    def request_key(self):
        """
        Request a new quantum key
        """
        data = request.get_json()

        if not data or 'peer_manager_id' not in data:
            return jsonify({'error': 'Missing peer_manager_id'}), 400

        key_length = data.get('key_length', 256)

        try:
            # Generate quantum key via QKD
            quantum_key, key_id = self.qkd_channel.establish_key_pair(
                self.key_manager.manager_id,
                data['peer_manager_id']
            )

            # Store in key manager
            metadata = {
                'peer': data['peer_manager_id'],
                'purpose': data.get('purpose', 'email_encryption'),
                'key_length': key_length
            }
            self.key_manager.store_key(quantum_key, key_id, metadata)

            return jsonify({
                'key_id': key_id,
                'quantum_key': quantum_key.hex(),
                'metadata': metadata
            }), 201

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    def get_key(self, key_id):
        """
        Retrieve a quantum key by ID
        """
        quantum_key = self.key_manager.get_key(key_id)

        if quantum_key is None:
            return jsonify({'error': 'Key not found or expired'}), 404

        return jsonify({
            'key_id': key_id,
            'quantum_key': quantum_key.hex()
        }), 200

    def list_keys(self):
        """
        List all available keys
        """
        keys = self.key_manager.list_keys()
        return jsonify({'keys': keys}), 200

    def delete_key(self, key_id):
        """
        Delete a quantum key
        """
        success = self.key_manager.delete_key(key_id)

        if success:
            return jsonify({'message': 'Key deleted successfully'}), 200
        else:
            return jsonify({'error': 'Key not found'}), 404

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """
        Start the API server
        """
        self.app.run(host=host, port=port, debug=debug)
