import csv
import io
from gzip import GzipFile
from io import TextIOWrapper, StringIO

import pandas as pd
from pandas import DataFrame


class FileLoader:

    def load_head(self, rows: int) -> list[str]:
        pass

    def load_data_frame(self, start_row: int) -> DataFrame:
        pass


class LocalFileLoader(FileLoader):

    def __init__(self, path: str) -> None:
        self.path = path

    def load_head(self, rows) -> list[str]:
        with open(self.path) as input_file:
            return [next(input_file) for _ in range(rows)]

    def load_data_frame(self, start_row) -> DataFrame:
        return pd.read_csv(self.path, na_filter=False, skiprows=list(range(0, start_row)))


class AWSFileLoader(FileLoader):

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

    def load_data_frame(self, start_row: int) -> DataFrame:
        csv_obj = self.s3.get_object(Bucket=self.bucket, Key=self.key)
        body = csv_obj['Body']
        csv_string = body.read().decode('utf-8')

        return pd.read_csv(StringIO(csv_string), na_filter=False, skiprows=list(range(0, start_row)))
