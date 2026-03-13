import os
import requests
import jwt
from functools import wraps
from flask import request, jsonify, g

ISSUER = os.environ.get('OIDC_ISSUER', 'http://localhost:8080/realms/health')
AUD = os.environ.get('OIDC_AUDIENCE', 'health-api')

# ─────────────────────────────────────────
# TEST MODE — skip real Keycloak when testing
# Set TESTING=true environment variable
# ─────────────────────────────────────────
TESTING = os.environ.get('TESTING', 'false').lower() == 'true'

def _jwks():
    r = requests.get(f"{ISSUER}/.well-known/openid-configuration", timeout=5)
    jwks_uri = r.json()['jwks_uri']
    return requests.get(jwks_uri).json()

def verify_jwt(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # In test mode, inject a fake user from header
        if TESTING:
            role = request.headers.get('X-Test-Role', 'editor')
            g.user = {
                'preferred_username': 'test_user',
                'realm_access': {'roles': [role]},
                'resource_access': {}
            }
            return fn(*args, **kwargs)

        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return jsonify({'error': 'missing token'}), 401
        token = auth.split(' ', 1)[1]
        try:
            jwks = _jwks()
            decoded = jwt.decode(
                token,
                options={"verify_signature": False, "verify_aud": False},
                audience=AUD
            )
            g.user = decoded
            return fn(*args, **kwargs)
        except Exception as e:
            print("JWT decode error:", e)
            return jsonify({'error': 'invalid token'}), 401
    return wrapper

def require_roles(roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = getattr(g, 'user', {})
            realm_roles = user.get('realm_access', {}).get('roles', [])
            client_roles = user.get('resource_access', {}).get(AUD, {}).get('roles', [])
            if any(role in realm_roles or role in client_roles for role in roles):
                return fn(*args, **kwargs)
            return jsonify({'error': 'forbidden'}), 403
        return wrapper
    return deco