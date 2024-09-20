from langsmith import unit

from my_agent.model.user import UserInfo
from my_agent.retrievers.transaction_retriever import TransactionRetriever
import pytest
import csv
import logging

from my_agent.tools.process_transactions import load_transactions

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
    bank_statement_retriever = TransactionRetriever()
    simple_transaction_results = bank_statement_retriever.classify_transactions(simple_transactions)

    log.info(simple_transaction_results)

    for transaction in simple_transaction_results:
        expected = next((expected for expected in expected_simple_transaction_results if expected["Unique Id"] == transaction["Unique Id"]), None)
        assert expected["transaction_type"] == transaction["transaction_type"]


@unit
def test_filter_transactions_with_balance(simple_transactions_with_balance):
    bank_statement_retriever = TransactionRetriever()
    simple_transaction_results = bank_statement_retriever.classify_transactions(simple_transactions_with_balance[:10])

    log.info(simple_transaction_results)
    test1 = False
    test2 = False
    test3 = False

    for transaction, transaction_type in zip(simple_transactions_with_balance[:10], simple_transaction_results):
        if transaction["Details"] == "Loan Payment":
            assert transaction_type['transaction_type'] == "capital deposit"
            test1 = True
        if transaction["Details"] == "Loan Interest":
            assert transaction_type['transaction_type'] == "loan interest"
            test2 = True
        if transaction["Details"] == "Loan Payment Reversal":
            assert transaction_type['transaction_type'] == "capital deposit reversal" or transaction_type['transaction_type'] == "capital withdrawal"
            test3 = True

    assert test1
    assert test2
    assert test3


@unit
def test_classify_property_management_statement(property_management_transactions):
    statement_retriever = TransactionRetriever()
    classified_results = statement_retriever.classify_transactions(property_management_transactions['transactions'])

    merged = [transaction | transaction_type for transaction, transaction_type in zip(property_management_transactions['transactions'], classified_results)]
    july = [transaction for transaction in merged if transaction['date'] == 'Jul 2023']
    log.info(july)

    july_management = next(t for t in july if t['description'] == 'Management fee')
    july_rent = next(t for t in july if t['description'] == 'Rent')
    july_water_rates = next(t for t in july if t['description'] == 'Water rates')
    july_water_usage = next(t for t in july if t['description'] == 'Water usage')

    assert july_management['moneyOut'] == 164.32
    assert july_management['transaction_type'] == 'property management'

    assert july_rent['moneyIn'] == 2600
    assert july_rent['transaction_type'] == 'rental income'

    assert july_water_rates['moneyOut'] == 173.37
    assert july_water_rates['transaction_type'] == 'water'

    assert july_water_usage['moneyIn'] == 180.0
    assert july_water_usage['transaction_type'] == 'water refund'


@unit
def test_classify_single_transaction():
    bank_statement_retriever = TransactionRetriever()
    singleton_list = [{'date': 'Mar 2024', 'description': 'Water rates', 'amount': 134.37}]
    simple_transaction_results = bank_statement_retriever.classify_transactions(singleton_list)

    log.info(simple_transaction_results)
    for transaction, transaction_type in zip(singleton_list, simple_transaction_results):
        t = transaction | transaction_type
        assert t["description"] == "Water rates"
        assert t["transaction_type"] == "water"



