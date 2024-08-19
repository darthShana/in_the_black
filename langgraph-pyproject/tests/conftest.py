import boto3
import logging

import pandas as pd
import pytest
from boto3.dynamodb.conditions import Key

from my_agent.model.chart_of_accounts import default_chart_of_accounts
from my_agent.model.transaction import BankAccountTypeEnum
from tests.test_process_bank_export import customer_number
from my_agent.tools.process_bank_export import classify_transaction, save_classified_transactions

log = logging.getLogger(__name__)
dynamodb = boto3.resource('dynamodb')


@pytest.fixture(scope='session')
def s3_client():
    return boto3.client('s3')


@pytest.fixture
def sample_transaction_file():
    return pd.read_csv('tests/data/Export20240727172157_inputs.csv')


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


@pytest.fixture(scope="session")
def upload_transactions(s3_client, transaction_filter):
    table = dynamodb.Table('Transactions')
    response = table.query(
        IndexName='CustomerIndex',
        KeyConditionExpression=Key('CustomerNumber').eq(customer_number)
    )

    with table.batch_writer() as batch:
        for item in response['Items']:
            batch.delete_item(Key={
                "TransactionID": item["TransactionID"]
            })

    s3_client.upload_file('tests/data/Export20240727172157.csv', "black-transactions-8e8f04a", f"{customer_number}/Export20240727172157.csv")
    s3_client.upload_file('tests/data/Export20240804075341.csv', "black-transactions-8e8f04a", f"{customer_number}/Export20240804075341.csv")

    t1 = classify_transaction('Export20240727172157.csv', None)
    save_classified_transactions(BankAccountTypeEnum.COMPANY_ACCOUNT, t1)
    t2 = classify_transaction('Export20240804075341.csv', transaction_filter, )
    save_classified_transactions(BankAccountTypeEnum.PERSONAL_ACCOUNT, t2)
    return True

