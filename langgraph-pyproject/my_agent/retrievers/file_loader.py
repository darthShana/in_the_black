import base64
import csv
import io
import json
import logging
import os

import requests
from langchain_core.utils.json import parse_json_markdown
from io import StringIO

import pandas as pd
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from pandas import DataFrame

from my_agent.retrievers.header_filter import HeaderFilter
log = logging.getLogger(__name__)


class FileLoader:

    def extract_transactions(self) -> list[dict]:
        pass


class LocalCSVFileLoader(FileLoader):

    def __init__(self, path: str) -> None:
        self.path = path

    def extract_transactions(self) -> list[dict]:
        head = self.load_head(20)
        header_filter = HeaderFilter()
        f = header_filter.lines_to_skip(head)
        return self.load_data_frame(f['line_number']).to_dict("records")

    def load_head(self, rows) -> list[str]:
        with open(self.path) as input_file:
            return [next(input_file) for _ in range(rows)]

    def load_data_frame(self, start_row) -> DataFrame:
        return pd.read_csv(self.path, na_filter=False, skiprows=list(range(0, start_row)))


class AWSCSVFileLoader(FileLoader):

    def __init__(self, client, bucket: str, key: str) -> None:
        self.bucket = bucket
        self.key = key
        self.s3 = client

    def extract_transactions(self) -> list[dict]:
        head = self.load_head(20)
        header_filter = HeaderFilter()
        f = header_filter.lines_to_skip(head)
        return self.load_data_frame(f['line_number']).to_dict("records")

    def load_head(self, rows: int) -> list[str]:
        response = self.s3.get_object(Bucket=self.bucket, Key=self.key)
        cr = csv.reader(io.TextIOWrapper(response['Body'], encoding="utf-8"))

        ret = []
        while line := next(cr, None):
            ret.append(", ".join(line))
            if len(ret) >= rows:
                return ret

        return ret

    def load_data_frame(self, start_row: int) -> DataFrame:
        csv_obj = self.s3.get_object(Bucket=self.bucket, Key=self.key)
        body = csv_obj['Body']
        csv_string = body.read().decode('utf-8')

        return pd.read_csv(StringIO(csv_string), na_filter=False, skiprows=list(range(0, start_row)))


class AWSPDFFileLoader(FileLoader):

    def __init__(self, client, bucket: str, key: str) -> None:
        self.bucket = bucket
        self.key = key
        self.s3 = client
        self.model = ChatAnthropic(model="claude-3-5-sonnet-20240620")
        self.api_url = "https://9x3mpoyac7.execute-api.us-east-1.amazonaws.com/example-stage-c964138/convert"

    def extract_transactions(self) -> list[dict]:
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
        images_base64 = result['images']
        log.info(f"loaded images: {len(images_base64)}")

        transactions = []
        for image in images_base64:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", """
                                You are a bookkeeper for a residential rental company. 
                                Extract a list of transactions present in statement. include the date, description and amount in every transaction, in addition to any other info present
                                Extract the result in json format marking the json as ```json:"""),
                    (
                        "user", [
                            {
                                "type": "image_url",
                                "image_url": {"url": "data:image/png;base64,{image_data}"},
                            }
                        ]

                    ),
                ]
            )
            chain = prompt | self.model
            response = chain.invoke({"image_data": image})
            log.info(response)
            markdown = parse_json_markdown(response.content)
            transactions.extend(markdown)

        return transactions

