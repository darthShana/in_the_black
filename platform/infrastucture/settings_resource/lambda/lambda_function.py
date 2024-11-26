import json
import os


def handler(event, context):
    endpoint = os.environ['ENDPOINT']
    client_id = os.environ['CLIENT_ID']
    user_pool_id = os.environ['USER_POOL_ID']

    return {
        'statusCode': 200,
        'body': json.dumps({
            'endpoint': endpoint,
            'clientID': client_id,
            'pool': user_pool_id
        })
    }
