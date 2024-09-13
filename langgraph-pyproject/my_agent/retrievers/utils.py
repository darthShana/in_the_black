import base64
import os

import requests

COGNITO_DOMAIN = "in-the-black-auth.auth.us-east-1.amazoncognito.com"
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]


def escape_f_string(text):
    return text.replace('{', '{{').replace('}', '}}')


def escape_examples(examples):
    return [{k: escape_f_string(v) for k, v in example.items()} for example in examples]


def get_cognito_token():
    token_url = f"https://{COGNITO_DOMAIN}/oauth2/token"

    # Encode client_id and client_secret
    client_credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
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
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get token: {response.text}")