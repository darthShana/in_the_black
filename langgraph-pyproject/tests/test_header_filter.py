import logging

import pytest

from my_agent.retrievers.file_loader import FileLoader, LocalFileLoader
from my_agent.retrievers.header_filter import HeaderFilter
from langsmith import unit
log = logging.getLogger(__name__)


@pytest.fixture
def file_loader() -> FileLoader:
    return LocalFileLoader('tests/data/Export20240727172157.csv')


@unit
def test_lines_to_skip(file_loader):
    header_filter = HeaderFilter(file_loader)
    f = header_filter.lines_to_skip()
    assert f['headers'] == "Date,Unique Id,Tran Type,Cheque Number,Payee,Memo,Amount"
    assert f['line_number'] == 5


@unit
def test_load_transactions_from_file(file_loader):
    header_filter = HeaderFilter(file_loader)
    df = header_filter.extract_transactions()

    # Date, Unique Id, Tran Type, Cheque Number, Payee, Memo, Amount
    # 2023/04/01, 2023040101, LOAN INT,, "LOAN - INTEREST", "12-3273-0018314-92 001 INTEREST", -796.92
    transaction = df.loc[0].to_dict()
    assert transaction['Date'] == "2023/04/01"
    assert transaction['Unique Id'] == 2023040101
    assert transaction['Tran Type'] == "LOAN INT"
    assert transaction['Payee'] == "LOAN - INTEREST"
    assert transaction['Memo'] == "12-3273-0018314-92 001 INTEREST"
    assert transaction['Amount'] == -796.92
