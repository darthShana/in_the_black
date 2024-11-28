import base64
import csv
import io
import json
import logging
from datetime import datetime
from typing import Union

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
        response = self.s3.get_object(Bucket=self.bucket, Key=self.key)
        pdf_bytes = response['Body'].read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        payload = json.dumps({"body": pdf_base64})

        token = get_cognito_token()

        headers = {
            'Content-Type': 'application/json',
            "Authorization": f"Bearer {token}"
        }
        log.info('posting to pdf converter')
        response = requests.post(self.api_url, data=payload, headers=headers)
        log.info(response.headers)
        result = json.loads(response.text)
        return result['images']

