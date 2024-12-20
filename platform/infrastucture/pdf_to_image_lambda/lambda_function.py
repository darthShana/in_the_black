import datetime
import json
import boto3
from pdf2image import convert_from_bytes
from io import BytesIO


def handler(event, context):
    for record in event['Records']:
        # Parse message
        message = json.loads(record['body'])
        job_id = message['job_id']
        bucket = message['bucket']
        object_key = message['object_key']

        # Initialize S3 client
        s3 = boto3.client('s3')
        try:

            # Update status to processing
            status = {
                'status': 'processing',
                'object_key': object_key,
                'started_at': str(datetime.datetime.now())
            }
            s3.put_object(
                Bucket=bucket,
                Key=f"{object_key}/{job_id}/status.json",
                Body=json.dumps(status),
                ContentType='application/json'
            )

            # Get the PDF from S3
            response = s3.get_object(Bucket=bucket, Key=object_key)
            pdf_content = response['Body'].read()

            # Convert PDF to images
            images = convert_from_bytes(pdf_content, fmt='png')

            # Upload each image to S3
            image_keys = []
            for idx, img in enumerate(images):
                img = img.convert('RGB')
                buffered = BytesIO()
                img.save(buffered, format="JPEG", quality=85, optimize=True)
                buffered.seek(0)

                image_key = f"{object_key}/{idx}.jpg"
                s3.upload_fileobj(buffered, bucket, image_key)
                image_keys.append(image_key)

            # Update final status
            status = {
                'status': 'completed',
                'object_key': object_key,
                'image_keys': image_keys,
                'total_pages': len(images),
                'completed_at': str(datetime.datetime.now())
            }

            s3.put_object(
                Bucket=bucket,
                Key=f"{object_key}/{job_id}/status.json",
                Body=json.dumps(status),
                ContentType='application/json'
            )

        except Exception as e:
            # Update error status
            error_status = {
                'status': 'failed',
                'error': str(e),
                'failed_at': str(datetime.datetime.now())
            }
            s3.put_object(
                Bucket=bucket,
                Key=f"{object_key}/{job_id}/status.json",
                Body=json.dumps(error_status),
                ContentType='application/json'
            )

