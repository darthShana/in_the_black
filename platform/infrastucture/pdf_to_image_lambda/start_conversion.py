import json
import os

import boto3
import uuid

# Initialize job status in S3
s3 = boto3.client('s3')
# Initialize SQS client
sqs = boto3.client('sqs')


def handler(event, context):

    print(event['body'])
    # Parse the request

    loads = json.loads(event['body'])
    object_key = loads['object_key']
    bucket = os.environ['BUCKET']
    queue_url = os.environ["SQS_QUEUE_URL"]

    # Generate job ID
    job_id = str(uuid.uuid4())
    print(f"init job {job_id}")

    # Send message to SQS queue
    message = {
        'job_id': job_id,
        'bucket': bucket,
        'object_key': object_key
    }

    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(message)
    )

    status = {
        'status': 'processing',
        'object_key': object_key,
        'job_id': job_id
    }

    s3.put_object(
        Bucket=bucket,
        Key=f"{object_key}/{job_id}/status.json",
        Body=json.dumps(status),
        ContentType='application/json'
    )

    return {
        'statusCode': 202,  # Accepted
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # For CORS support
            'Access-Control-Allow-Methods': 'POST,OPTIONS'
        },
        'body': json.dumps({
            'job_id': job_id,
            'object_key': object_key,
            'status': 'processing'
        }
        )
    }


