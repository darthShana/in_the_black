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


@pytest.fixture
def simple_transactions_with_balance() -> list[dict]:
    file = open("tests/data/transactions_with_balance.csv", "r")
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
def test_filter_transactions_with_balance(simple_transactions_with_balance):
    bank_statement_retriever = BankStatementRetriever()
    simple_transaction_results = bank_statement_retriever.classify_transactions(simple_transactions_with_balance[:10])

    log.info(simple_transaction_results)
    for transaction, transaction_type in zip(simple_transactions_with_balance[:10], simple_transaction_results):
        if transaction["Details"] == "Loan Payment":
            assert transaction_type['transaction_type'] == "capital deposit"
        if transaction["Details"] == "Loan Interest":
            assert transaction_type['transaction_type'] == "loan interest"
