import requests
import base64
import json

# Replace these with your actual values
COGNITO_DOMAIN = "in-the-black-auth.auth.us-east-1.amazoncognito.com"
CLIENT_ID = "723dvmfb5nb8v556np7e4t25mr"
CLIENT_SECRET = "1rgeoovdmveiaumvapj9v7e77dhkdvbg10ps52itrgciuq2uee61"
API_ENDPOINT = "https://1z06866gye.execute-api.us-east-1.amazonaws.com/stage-177e7b6/valuation"


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
        "scope": "property-valuation/read"
    }

    response = requests.post(token_url, headers=headers, data=body)

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to get token: {response.text}")


def call_api(token, endpoint):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    data = {
        'address': '22 Fort Lincoln Loop,'
    }

    response = requests.post(f"{API_ENDPOINT}/{endpoint}",
                             headers=headers,
                             data=json.dumps(data)
                             )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API call failed: {response.text}")


# Main execution
try:
    # Get the JWT token
    token = get_cognito_token()
    print("Successfully obtained JWT token")

    # Call the API
    result = call_api(token, "your-endpoint")
    print("API Response:", json.dumps(result, indent=2))

except Exception as e:
    print(f"An error occurred: {str(e)}")