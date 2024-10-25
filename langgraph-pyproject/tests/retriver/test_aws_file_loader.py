import logging
from datetime import datetime

from langsmith import unit

from my_agent.retrievers.file_loader import AWSCSVFileLoader

log = logging.getLogger(__name__)


def is_valid_date(date_string):
    try:
        # Attempt to parse the date string
        datetime.strptime(date_string, '%Y/%m/%d')
        return True
    except ValueError:
        return False


@unit
def test_aws_file_loader(s3_client):
    loader = AWSCSVFileLoader(
            client=s3_client,
            bucket="black-transactions-8e8f04a",
            key="b07d4732-6675-4a98-a45f-c2fa714262db/Export20240727172157.csv")

    head = loader.load_head(20)
    log.info(head)
    assert len(head) == 20


@unit
def test_filter_content(s3_client):
    loader = AWSCSVFileLoader(
        client=s3_client,
        bucket="black-transactions-8e8f04a",
        key="b07d4732-6675-4a98-a45f-c2fa714262db/Export20240727172157.csv"
    )
    df = loader.load_content()
    assert 'Date' in df.columns, "DataFrame does not have a 'Date' column"
    assert df['Date'].notnull().all(), "Some rows have null values in the 'Date' column"
    assert df['Date'].apply(is_valid_date).all(), "Some rows have invalid date values in the 'Date' column"

