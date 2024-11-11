import json
import logging
import os
import uuid
from datetime import datetime

import requests

import boto3
import jwt

from jwt.algorithms import RSAAlgorithm
from boto3.dynamodb.conditions import Key

# Initialize the DynamoDB client
dynamo = boto3.client('dynamodb')
dynamodb = boto3.resource('dynamodb')

user_table = dynamodb.Table('Users')

# Get the table
log = logging.getLogger(__name__)

USER_POOL_ID = os.environ['USER_POOL_ID']
CLIENT_ID = os.environ["CLIENT_ID"]
REGION = os.environ["AWS_DEFAULT_REGION"]


def verify_token(token: str):
    # Get the JWT headers
    headers = jwt.get_unverified_header(token)

    # Get the key id from the headers
    kid = headers['kid']

    # Get the public keys from Cognito
    keys_url = f'https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json'
    response = requests.get(keys_url)
    keys = response.json()['keys']

    # Find the correct public key
    public_key = None
    for key in keys:
        if key['kid'] == kid:
            public_key = RSAAlgorithm.from_jwk(key)
            break

    if not public_key:
        raise ValueError('Public key not found')

    # Verify the token
    try:
        payload = jwt.decode(
            token,
            public_key,
            algorithms=['RS256'],
            options={'verify_exp': True}
        )
        # Manually verify the client_id (audience)
        if payload.get('client_id') != CLIENT_ID:
            raise ValueError('Token was not issued for this audience')

        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError('Token has expired')
    except jwt.InvalidTokenError:
        raise ValueError('Invalid token')


def handler(event, context):

    try:
        # Get the Authorization header
        auth_header = event['headers'].get('authorization')
        print(f"header: {event['headers']}")
        if not auth_header or not auth_header.startswith('Bearer '):
            return {
                'statusCode': 401,
                'body': json.dumps('Unauthorized: Invalid token')
            }

        # Extract the token
        token = auth_header.split(' ')[1]

        # Decode and verify the token (replace with your own secret key and algorithm)
        decoded_token = verify_token(token)

        # Extract username from the token
        email = decoded_token.get('username')
        print(f"username: {email}")

        response = user_table.query(
            IndexName='EmailIndex',
            KeyConditionExpression=Key('UserEmail').eq(email)
        )

        if response['Items']:
            user = response['Items'][0]
            log.info(f"user {user}")

            user_id = user['UserID']

            body = json.loads(event['body'])
            print(f"body: {body}")

            if body.get('accepted_anomaly') is not None:
                accepted_anomaly = body.get('accepted_anomaly')
                date_object = datetime.strptime(accepted_anomaly['period'], "%B %Y").date()
                dynamo.put_item(TableName="AcceptedAnomalies", Item={
                        'Id': {'S': str(uuid.uuid4())},
                        'UserId': {'S': user_id},
                        'Date': {'S': date_object.strftime("%Y/%m/%d")},
                        'Period': {'S': accepted_anomaly['period']},
                        'Insight': {'S': accepted_anomaly['insight']},
                        'AcceptReason': {'S': accepted_anomaly['accept_reason']},
                    }
                )

                return {
                    'statusCode': 200,
                    'body': json.dumps('Anomaly accepted successfully.')
                }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Internal server error: {str(e)}')
        }
