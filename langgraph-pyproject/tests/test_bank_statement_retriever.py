from langsmith import unit
from my_agent.retrievers.bank_statement_retriever import BankStatementRetriever
import pytest
import csv
import logging
from pprint import pprint
log = logging.getLogger(__name__)


@pytest.fixture
def simple_transactions() -> list[dict]:
    file = open("tests/data/Export20240727172157_inputs.csv", "r")
    data = list(csv.DictReader(file, delimiter=","))
    file.close()
    return data


@pytest.fixture
def filter_transactions() -> list[dict]:
    file = open("tests/data/Export20240804075341_inputs.csv", "r")
    data = list(csv.DictReader(file, delimiter=","))
    file.close()
    return data


@pytest.fixture
def expected_simple_transaction_results() -> list[dict]:
    file = open("tests/data/Export20240727172157_results.csv", "r")
    data = list(csv.DictReader(file, delimiter=","))
    file.close()
    return data


@unit
def test_bank_statement_retriever(simple_transactions, expected_simple_transaction_results):
    bank_statement_retriever = BankStatementRetriever()
    simple_transaction_results = bank_statement_retriever.classify_transactions(simple_transactions)

    log.info(simple_transaction_results)

    for transaction in simple_transaction_results:
        expected = next((expected for expected in expected_simple_transaction_results if expected["Unique Id"] == transaction["Unique Id"]), None)
        assert expected["transaction_type"] == transaction["transaction_type"]


@unit
def test_bank_statement_retriever_with_filter(filter_transactions):
    bank_statement_retriever = BankStatementRetriever()
    transaction_filter = {
        '$or': [
            {
                '$and': [
                    {'Payee': {'$contain': 'AUCKLAND COUNCIL'}},
                    {'Memo': {'$contain': '34 Nicholas'}}
                ]
            }, {
                'Memo': {'$contain': 'D/D 5398975-01 WATERCARE'}
            }, {
                'Payee': {'$contain': 'ASB BANK Insurance'}
            }
        ]
    }
    filtered_transaction_results = bank_statement_retriever.filter_transactions(filter_transactions, transaction_filter)
    assert len(filtered_transaction_results) == 25
