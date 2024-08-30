import boto3
import logging

import pandas as pd
import pytest
from boto3.dynamodb.conditions import Key

from my_agent.model.chart_of_accounts import default_chart_of_accounts
from my_agent.model.transaction import BankAccountTypeEnum
from tests.test_process_bank_export import customer_number
from my_agent.tools.process_bank_export import save_classified_transactions, classify_transactions

log = logging.getLogger(__name__)
dynamodb = boto3.resource('dynamodb')


@pytest.fixture(scope='session')
def s3_client():
    return boto3.client('s3')


@pytest.fixture
def sample_transaction_file():
    return pd.read_csv('tests/data/Export20240727172157_inputs.csv')


@pytest.fixture
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


@pytest.fixture
def sample_transaction_types():
    return pd.read_csv('tests/data/Export20240727172157_results.csv')


@pytest.fixture
def sample_transaction_overrides():
    return pd.read_csv('tests/data/transaction_overrides.csv')


@pytest.fixture
def chart_of_accounts():
    return default_chart_of_accounts


@pytest.fixture(scope='session')
def transaction_filter():
    return {
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


