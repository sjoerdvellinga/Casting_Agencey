import json
from os import environ as env
from functools import wraps
from datetime import datetime, timedelta
from urllib.request import urlopen
import os

from jose import jwt

from flask import request

from dotenv import load_dotenv
load_dotenv()

# Use auth0 for user authorization
# AuthError Exception

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def check_access_token():
    # Get the "Authorization" header from the request
    auth_header = request.headers.get("Authorization")

    # Check if the header exists and starts with "Bearer "
    if auth_header and auth_header.startswith("Bearer "):
        # Extract the token part (remove "Bearer " prefix)
        access_token = auth_header.split(" ")[1]
        return access_token
    else:
        return None

## Auth Header
def get_token_auth_header():
    """
    Obtains the access token from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth:
        raise AuthError(
            {
                "code": "authorization_header_missing",
                "description": "Authorization header is expected"
            }, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must start with"
                " Bearer"
            }, 401)
    elif len(parts) == 1:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Token not found"
            }, 401)
    elif len(parts) > 2:
        raise AuthError(
            {
                "code": "invalid_header",
                "description": "Authorization header must be"
                " Bearer token"
            }, 401)

    token = parts[1]
    return token


def check_permissions(permission, payload):
    """
    Helper which checks if the decoded JWT has the required permission
    """
    if payload.get('permissions'):
        token_scopes = payload.get("permissions")
        if (permission not in token_scopes):
            raise AuthError(
                {
                    'code': 'invalid_permissions',
                    'description': 'User does not have enough privileges'
                }, 401)
        else:
            return True
    else:
        raise AuthError(
            {
                'code': 'invalid_permissions',
                'description': 'User does not have any roles attached'
            }, 401)


def verify_decode_jwt(token):
    """
    Receives the encoded token and validates it after decoded
    """
    jsonurl = urlopen(f'https://{env.get("AUTH0_DOMAIN")}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError(
            {
                'code': 'invalid_header',
                'description': 'Authorization malformed.'
            }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    if rsa_key:
        try:
            payload = jwt.decode(token,
                                 rsa_key,
                                 algorithms=env.get("ALGORITHMS"),
                                 audience=env.get("API_AUDIENCE"),
                                 issuer='https://' + env.get("AUTH0_DOMAIN") + '/')

            return payload

        except jwt.ExpiredSignatureError as exc:
            raise AuthError(
                {
                    'code': 'token_expired',
                    'description': 'Token expired.'
                }, 401) from exc

        except jwt.JWTClaimsError as exc:
            raise AuthError(
                {
                    'code': 'invalid_claims',
                    'description': 'Incorrect claims. Please, check the audience and issuer.'
                }, 401) from exc
        except Exception as exc:
            raise AuthError(
                {
                    'code': 'invalid_header',
                    'description': 'Unable to parse authentication token.'
                }, 400) from exc
    raise AuthError(
        {
            'code': 'invalid_header',
            'description': 'Unable to find the appropriate key.'
        }, 400)


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)
            return f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator

# Function to generate a test JWT token
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
def generate_test_token():
    # Define JWT payload with necessary claims (e.g., sub, exp, iss, aud, etc.)
    payload = {
        "sub": "Oo5YWoteG83V2i9Blk5TZ9jVy9UDrOqY@clients",
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iss": env.get("AUTH0_DOMAIN"),
        "aud": env.get("API_AUDIENCE"),
        "permissions": [
            "delete:actor",
            "delete:movie",
            "post:actor",
            "post:actor-cast",
            "post:cast",
            "post:movie",
            "read:actor_portfolio",
            "read:actors",
            "read:cast",
            "read:movies",
            "update:movie"
  ]
    }