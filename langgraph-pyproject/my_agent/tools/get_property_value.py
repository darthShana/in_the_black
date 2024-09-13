import os

import requests
import base64
import json

from my_agent.retrievers.utils import get_cognito_token

# Replace these with your actual values
API_ENDPOINT = "https://jtk21yuyi2.execute-api.us-east-1.amazonaws.com/prod-9c56ae7"


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
    result = call_api(token, "valuation")
    print("API Response:", json.dumps(result, indent=2))

except Exception as e:
    print(f"An error occurred: {str(e)}")