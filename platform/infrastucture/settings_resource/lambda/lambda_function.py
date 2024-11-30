import json
import os


def handler(event, context):
    endpoint = os.environ['ENDPOINT']
    client_id = os.environ['CLIENT_ID']
    user_pool_id = os.environ['USER_POOL_ID']
    langgraph_api_key = os.environ['LANGGRAPH_API_KEY']

    return {
        'statusCode': 200,
        'body': json.dumps({
            'endpoint': endpoint,
            'clientID': client_id,
            'pool': user_pool_id,
            'langgraph_api_endpoint': 'https://accountingassistant-d607474a4dad5c7ebb0d09000478910f.default.us.langgraph.app',
            'langgraph_api_key': langgraph_api_key,
        })
    }
