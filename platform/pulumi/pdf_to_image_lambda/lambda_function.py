import json
import base64
from pdf2image import convert_from_bytes
from io import BytesIO


def handler(event, context):
    try:
        # Get the PDF content from the request body
        pdf_content = base64.b64decode(event['body'])

        # Convert PDF to image
        images = convert_from_bytes(pdf_content, fmt='png')

        images_strings = []
        for img in images:
            img = img.convert('RGB')
            # Save the image to a BytesIO object
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=85, optimize=True)
            images_strings.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))

        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'images': images_strings})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }