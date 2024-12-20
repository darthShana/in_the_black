import base64
import csv
import io
import json
import logging
import time
from datetime import datetime
from typing import Union
from botocore.exceptions import ClientError

import requests
from io import StringIO

import pandas as pd
from pandas import DataFrame

from my_agent.retrievers.header_filter import HeaderFilter
from my_agent.retrievers.utils import get_cognito_token

log = logging.getLogger(__name__)


class FileLoader:

    def load_content(self) -> Union[list[str], pd.DataFrame]:
        pass


class LocalCSVFileLoader(FileLoader):

    def __init__(self, path: str) -> None:
        self.path = path

    def load_head(self, rows) -> list[str]:
        with open(self.path) as input_file:
            return [next(input_file) for _ in range(rows)]

    def load_content(self) -> DataFrame:
        head = self.load_head(20)
        header_filter = HeaderFilter()
        f = header_filter.lines_to_skip(head)

        return pd.read_csv(self.path, na_filter=False, skiprows=list(range(0, f['line_number'])))


# Function to check if a value is not null and not an empty string
def is_not_empty(value):
    if pd.isna(value):
        return False
    if isinstance(value, str) and value.strip() == '':
        return False
    return True


class AWSCSVFileLoader(FileLoader):

    def __init__(self, client, bucket: str, key: str) -> None:
        self.bucket = bucket
        self.key = key
        self.s3 = client

    def load_head(self, rows: int) -> list[str]:
        response = self.s3.get_object(Bucket=self.bucket, Key=self.key, Range='bytes=0-2048')
        content = response['Body'].read().decode('utf-8')
        csv_reader = csv.reader(StringIO(content))

        ret = []
        for i, row in enumerate(csv_reader):
            ret.append(", ".join(row))
            if len(ret) >= rows:
                return ret

        return ret

    def load_content(self) -> DataFrame:
        head = self.load_head(20)

        header_filter = HeaderFilter()
        f = header_filter.lines_to_skip(head)

        csv_obj = self.s3.get_object(Bucket=self.bucket, Key=self.key)
        body = csv_obj['Body']
        csv_string = body.read().decode('utf-8')

        df = pd.read_csv(StringIO(csv_string), na_filter=False, skiprows=list(range(0, f['line_number'])))

        content_count = df.applymap(is_not_empty).sum(axis=1)
        filtered_df = df[content_count > 1]
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        #     log.info(filtered_df)
        return filtered_df


class AWSPDFFileLoader(FileLoader):

    def __init__(self, client, bucket: str, key: str) -> None:
        self.bucket = bucket
        self.key = key
        self.s3 = client
        self.api_url = "https://app.accountingassistant.io/convert-pdf-to-image"

    def load_content(self) -> list[str]:
        try:
            # Try to head the object
            self.s3.head_object(Bucket=self.bucket, Key=f"{self.key}/")
            return self.read_processed_images()
        except ClientError as e:
            # If error code is 404, directory doesn't exist
            if e.response['Error']['Code'] == '404':
                payload = {
                    "object_key": self.key,
                }

                token = get_cognito_token()

                headers = {
                    'Content-Type': 'application/json',
                    "Authorization": f"Bearer {token}"
                }
                log.info('posting to pdf converter')
                response = requests.post(self.api_url, data=json.dumps(payload), headers=headers)
                log.info(response.text)
                job = json.loads(response.text)

                # Start polling
                start_time = time.time()
                status_key = f"{self.key}/{job['job_id']}/status.json"

                while (time.time() - start_time) < 300:
                    try:
                        # Check if status.json exists
                        response = self.s3.get_object(Bucket=self.bucket, Key=status_key)
                        status_data = json.loads(response['Body'].read().decode('utf-8'))

                        # Check if status is completed
                        if status_data.get('status') == 'completed':
                            log.info("Process completed successfully")
                            return self.read_processed_images()

                        log.info(f"Status not completed yet: {status_data.get('status')}")
                    except ClientError as e:
                        if e.response['Error']['Code'] == 'NoSuchKey':
                            log.info(f"Status file not found yet, waiting...")
                        else:
                            raise

                    # Wait 10 seconds before next check
                    time.sleep(10)
            # For other errors, raise the exception
            raise

    def read_processed_images(self):
        jpg_files = []
        paginator = self.s3.get_paginator('list_objects_v2')

        for page in paginator.paginate(
                Bucket=self.bucket,
                Prefix=f"{self.key}/",
        ):
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith('.jpg'):
                        # Get the image content
                        log.info(f"getting process image: {obj['Key']}")
                        image_obj = self.s3.get_object(
                            Bucket=self.bucket,
                            Key=obj['Key']
                        )
                        image_content = image_obj['Body'].read()
                        # Convert to base64
                        base64_image = base64.b64encode(image_content).decode('utf-8')
                        jpg_files.append(base64_image)

        return jpg_files

