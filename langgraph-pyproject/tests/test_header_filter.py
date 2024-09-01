import logging

import pytest

from my_agent.retrievers.file_loader import FileLoader, LocalCSVFileLoader
from my_agent.retrievers.header_filter import HeaderFilter
from langsmith import unit
log = logging.getLogger(__name__)


@pytest.fixture
def file_loader() -> LocalCSVFileLoader:
    return LocalCSVFileLoader('tests/data/Export20240727172157.csv')


@unit
def test_lines_to_skip(file_loader):
    header_filter = HeaderFilter()
    head = file_loader.load_head(20)

    f = header_filter.lines_to_skip(head)
    assert f['headers'] == "Date,Unique Id,Tran Type,Cheque Number,Payee,Memo,Amount"
    assert f['line_number'] == 5


