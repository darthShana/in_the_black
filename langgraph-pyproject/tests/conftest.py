import csv
import os

import logging

import pandas as pd
import pytest

from my_agent.model.chart_of_accounts import default_chart_of_accounts
from my_agent.model.user import UserInfo
from my_agent.tools.process_transactions import load_transactions
from my_agent.utils.aws_credentials import AWSSessionFactory

log = logging.getLogger(__name__)
dynamodb = AWSSessionFactory().get_session().resource('dynamodb')


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    if 'no_cache' in item.keywords:
        if 'LANGCHAIN_TEST_CACHE' in os.environ:
            del os.environ['LANGCHAIN_TEST_CACHE']
    else:
        if 'LANGCHAIN_TEST_CACHE' not in os.environ:
            os.environ['LANGCHAIN_TEST_CACHE'] = 'tests/cassettes'


@pytest.hookimpl(trylast=True)
def pytest_runtest_teardown(item, nextitem):
    if 'LANGCHAIN_TEST_CACHE' in os.environ:
        del os.environ['LANGCHAIN_TEST_CACHE']


@pytest.fixture(scope='session')
def s3_client():
    return AWSSessionFactory().get_session().client('s3')


@pytest.fixture(scope='session')
def sample_transaction_file():
    return pd.read_csv('tests/data/Export20240727172157_inputs.csv')


@pytest.fixture
def simple_transactions_with_balance() -> list[dict]:
    file = open("tests/data/transactions_with_balance.csv", "r")
    data = list(csv.DictReader(file, delimiter=","))
    file.close()
    return data


@pytest.fixture(scope='session')
def property_management_transactions() -> dict[str, list[dict]]:
    mock_user = UserInfo(
        user_id='d3b0c891-41c6-49ba-95ee-4c33bf17cd3f',
        properties=[]
    )
    def mock_get_user(username):
        return mock_user

    return load_transactions('F Rental Statement.pdf')


@pytest.fixture(scope='session')
def sample_transaction_file2():
    df = pd.read_csv('tests/data/Export20240804075341_inputs.csv')
    filter_condition = df['Memo'].str.contains('D/D 5398975-01 WATERCARE|D/D 12345148793 34 Nicholas|D/D BATCH 015085 05 275945 01', case=False, na=False)
    filtered_df = df[filter_condition]

    def get_transaction_type(payee):
        payee = payee.lower()  # Convert to lowercase for case-insensitive matching
        if 'water' in payee:
            return 'water'
        elif 'auckland council' in payee:
            return 'rates'
        elif 'insurance' in payee:
            return 'insurance'
        else:
            return 'other'  # You can change this to whatever default you prefer

    filtered_df['transaction_type'] = filtered_df['Payee'].apply(get_transaction_type)
    return filtered_df


@pytest.fixture(scope='session')
def sample_transaction_types():
    return pd.read_csv('tests/data/Export20240727172157_results.csv')


@pytest.fixture(scope='session')
def sample_transaction_overrides():
    return pd.read_csv('tests/data/transaction_overrides.csv')


@pytest.fixture(scope='session')
def chart_of_accounts():
    return default_chart_of_accounts




