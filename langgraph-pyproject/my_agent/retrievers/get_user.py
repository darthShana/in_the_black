import logging
import os

import jwt
import requests
from boto3.dynamodb.conditions import Key

from jwt.algorithms import RSAAlgorithm
from my_agent.model.user import UserInfo, Property, PropertyTypeEnum
from my_agent.utils.aws_credentials import AWSSessionFactory

log = logging.getLogger(__name__)
USER_POOL_ID = os.environ['COGNITO_USER_POOL_ID']
CLIENT_ID = os.environ["COGNITO_USER_CLIENT_ID"]
REGION = os.environ["AWS_DEFAULT_REGION"]

# Initialize the DynamoDB client
aws = AWSSessionFactory()


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


class UserRetriever:

    @staticmethod
    def get_user(access_token: str) -> UserInfo:
        dynamodb = aws.get_session().resource('dynamodb')

        # Get the table
        table = dynamodb.Table('Users')

        payload = verify_token(access_token)
        email = payload.get('username')

        # Query the global secondary index
        response = table.query(
            IndexName='EmailIndex',
            KeyConditionExpression=Key('UserEmail').eq(email)
        )

        if response['Items']:
            user = response['Items'][0]
            log.info(f"user {user}")

            user_id = user['UserID']
            properties = []

            if 'properties' in user:
                for prop in user['properties']:
                    properties.append(Property(
                        property_id=prop['property_id'],
                        address1=prop['address1'],
                        suburb=prop['suburb'],
                        city=prop['city'],
                        property_type=PropertyTypeEnum(prop['property_type']),
                        bedrooms=prop['bedrooms'],
                    ))

            return UserInfo(
                # user_id='b5c7f883-eb98-4ef0-a744-1496510552c2'
                user_id=user_id,
                email=email,
                first_name=user['FirstName'],
                last_name=user['LastName'],
                properties=properties
            )
