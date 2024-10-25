import base64
import os

import requests
from functools import lru_cache
import time
# Global variables to store token information
access_token = None
refresh_token = None
token_expiry = 0

COGNITO_DOMAIN = "in-the-black-auth.auth.us-east-1.amazoncognito.com"
COGNITO_CLIENT_ID = os.environ["COGNITO_API_CLIENT_ID"]
COGNITO_CLIENT_SECRET = os.environ["COGNITO_API_CLIENT_SECRET"]


def escape_f_string(text):
    return text.replace('{', '{{').replace('}', '}}')


def escape_examples(examples):
    return [{k: escape_f_string(v) for k, v in example.items()} for example in examples]


def refresh_cognito_token():
    global access_token, refresh_token, token_expiry

    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    body = {
        "grant_type": "refresh_token",
        "client_id": COGNITO_CLIENT_ID,
        "refresh_token": refresh_token
    }

    response = requests.post(token_url, headers=headers, data=body)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        token_expiry = time.time() + token_data["expires_in"]
        return access_token
    else:
        # If refresh fails, clear the refresh token
        refresh_token = None
        return None


# Use LRU cache to store the result of get_cognito_token
@lru_cache(maxsize=1)
def cached_get_cognito_token():
    return get_cognito_token()


def get_cognito_token():
    global access_token, refresh_token, token_expiry
    current_time = time.time()

    # Check if we have a valid access token
    if access_token and current_time < token_expiry:
        return access_token

    # If we have a refresh token, try to use it
    if refresh_token and current_time < token_expiry + 3600:  # Assuming refresh token is valid for 1 hour after access token expiry
        new_token = refresh_cognito_token()
        if new_token:
            return new_token

    # If we don't have a valid token or refresh failed, get a new one
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"

    # Encode client_id and client_secret
    client_credentials = f"{COGNITO_CLIENT_ID}:{COGNITO_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(client_credentials.encode('utf-8')).decode('utf-8')

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {encoded_credentials}"
    }

    body = {
        "grant_type": "client_credentials",
        "scope": "api/read"
    }

    response = requests.post(token_url, headers=headers, data=body)

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data["access_token"]
        refresh_token = token_data.get("refresh_token")  # Not all flows return a refresh token
        token_expiry = current_time + token_data["expires_in"]
        return access_token
    else:
        raise Exception(f"Failed to get token: {response.text}")


if __name__ == "__main__":
    token = get_cognito_token()
    print(token)