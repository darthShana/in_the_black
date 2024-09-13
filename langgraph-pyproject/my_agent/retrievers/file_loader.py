import base64
import csv
import io
import json
import logging
from typing import Union

import requests
from io import StringIO

import pandas as pd
from pandas import DataFrame

from my_agent.retrievers.header_filter import HeaderFilter
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


class AWSCSVFileLoader(FileLoader):

    def __init__(self, client, bucket: str, key: str) -> None:
        self.bucket = bucket
        self.key = key
        self.s3 = client

    def load_head(self, rows: int) -> list[str]:
        response = self.s3.get_object(Bucket=self.bucket, Key=self.key)
        cr = csv.reader(io.TextIOWrapper(response['Body'], encoding="utf-8"))

        ret = []
        while line := next(cr, None):
            ret.append(", ".join(line))
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

        return pd.read_csv(StringIO(csv_string), na_filter=False, skiprows=list(range(0, f['line_number'])))


class AWSPDFFileLoader(FileLoader):

    def __init__(self, client, bucket: str, key: str) -> None:
        self.bucket = bucket
        self.key = key
        self.s3 = client
        self.api_url = "https://dutstfzmo0.execute-api.us-east-1.amazonaws.com/example-stage-c6f1078/convert"

    def load_content(self) -> list[str]:
        response = self.s3.get_object(Bucket=self.bucket, Key=self.key)
        pdf_bytes = response['Body'].read()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        payload = json.dumps({"body": pdf_base64})
        headers = {
            'Content-Type': 'application/json',
        }
        response = requests.post(self.api_url, data=payload, headers=headers)
        log.info('response form image conversion')
        log.info(response.headers)
        result = json.loads(response.text)
        return result['images']

