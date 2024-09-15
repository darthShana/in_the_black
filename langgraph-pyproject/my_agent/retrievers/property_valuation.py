import logging
import os

import requests
import base64
import json

from my_agent.model.user import Property, Valuation
from my_agent.retrievers.utils import get_cognito_token
log = logging.getLogger(__name__)

# Replace these with your actual values
API_ENDPOINT = "https://jtk21yuyi2.execute-api.us-east-1.amazonaws.com/prod-9c56ae7"


def call_api(token, property_data: Property):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    data = property_data.json()
    log.info(data)

    response = requests.post(f"{API_ENDPOINT}/valuation",
        headers=headers,
        data=data
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"API call failed: {response.text}")


def get_market_data(property_data: Property) -> Valuation:
    try:
        # Get the JWT token
        token = get_cognito_token()
        log.info("Successfully obtained JWT token")

        # Call the API
        result = call_api(token, property_data)
        log.info("API Response:", result)
        return Valuation.parse_obj(result)

    except Exception as e:
        log.error(f"An error occurred: {str(e)}")
