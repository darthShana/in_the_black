import json
import logging
import os
import requests

import boto3
import base64
import jwt

from jwt.algorithms import RSAAlgorithm
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Get the table
table = dynamodb.Table('Users')
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

        # Query the global secondary index
        response = table.query(
            IndexName='EmailIndex',
            KeyConditionExpression=Key('UserEmail').eq(email)
        )

        if response['Items']:
            user = response['Items'][0]
            log.info(f"user {user}")

            user_id = user['UserID']
            # Get the file content from the event body
            # Get the file content and filename from the event
            file_content = base64.b64decode(event['body'])
            content_disposition = event['headers'].get('content-disposition', '')
            filename = content_disposition.split('filename=')[1].strip('"') if 'filename=' in content_disposition else 'unknown_file'

            # Create the S3 object key
            s3_key = f"{user_id}/{filename}"
            print(f"s3_key: {s3_key}")

            # Upload the file to S3
            s3 = boto3.client('s3')
            bucket_name = os.environ['BUCKET_NAME']  # Store this in Lambda environment variables
            s3.put_object(Bucket=bucket_name, Key=s3_key, Body=file_content)

            return {
                'statusCode': 200,
                'body': json.dumps(f'File uploaded successfully. Object key: {s3_key}')
            }
        else:
            return {
                'statusCode': 400,
                'body': json.dumps('Bad Request: Username not found in token')
            }

    except jwt.InvalidTokenError:
        return {
            'statusCode': 401,
            'body': json.dumps('Unauthorized: Invalid token')
        }
    except ClientError as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error uploading file: {str(e)}')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Internal server error: {str(e)}')
        }
