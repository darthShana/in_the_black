import logging

import pytest
from langsmith import unit

from my_agent.retrievers.file_loader import LocalCSVFileLoader, AWSPDFFileLoader
log = logging.getLogger(__name__)


@pytest.fixture
def csv_file_loader() -> LocalCSVFileLoader:
    return LocalCSVFileLoader('tests/data/Export20240727172157.csv')


@pytest.fixture
def pdf_file_loader(s3_client) -> AWSPDFFileLoader:
    return AWSPDFFileLoader(s3_client, "black-transactions-8e8f04a", 'd3b0c891-41c6-49ba-95ee-4c33bf17cd3f/F Rental Statement.pdf')


@unit
def test_load_transactions_from_file(csv_file_loader):
    transactions = csv_file_loader.extract_transactions()

    # Date, Unique Id, Tran Type, Cheque Number, Payee, Memo, Amount
    # 2023/04/01, 2023040101, LOAN INT,, "LOAN - INTEREST", "12-3273-0018314-92 001 INTEREST", -796.92
    transaction = transactions[0]
    assert transaction['Date'] == "2023/04/01"
    assert transaction['Unique Id'] == 2023040101
    assert transaction['Tran Type'] == "LOAN INT"
    assert transaction['Payee'] == "LOAN - INTEREST"
    assert transaction['Memo'] == "12-3273-0018314-92 001 INTEREST"
    assert transaction['Amount'] == -796.92


@unit
def test_load_transactions_from_pdf(pdf_file_loader):
    test2 = pdf_file_loader.extract_transactions()
