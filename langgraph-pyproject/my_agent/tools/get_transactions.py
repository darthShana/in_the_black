import json
from datetime import datetime
from typing import List

import decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from pydantic.v1 import BaseModel, Field

from my_agent.model.transaction import Transaction

dynamodb = boto3.resource('dynamodb')


class GetTransactionsInput(BaseModel):
    start: datetime = Field(description="get transactions after this date and time")
    end: datetime = Field(description="get transactions before this date and time")


def to_transaction(i):
    return Transaction(
        transaction_id=i['TransactionID'],
        date=datetime.strptime(i['TransactionDate'], '%Y/%m/%d'),
        transaction_type=i['TransactionType'],
        amount=decimal.Decimal(i['TransactionAmount']),
        custom_id=i['CustomID'],
        bank_account_type=json.loads(i['BankAccountType'])
    )


def get_transactions(customer_number: str, start: datetime, end: datetime) -> List[Transaction]:
    table = dynamodb.Table('Transactions')

    date_attr = boto3.dynamodb.conditions.Attr('TransactionDate')
    customer_attr = boto3.dynamodb.conditions.Attr('CustomerNumber')
    response = table.scan(
        FilterExpression=
        customer_attr.eq(customer_number) &
        date_attr.between(start.strftime('%Y/%m/%d'), end.strftime('%Y/%m/%d'))
    )

    transactions = [to_transaction(i) for i in response['Items']]
    transactions.sort(key=lambda t: t.date, reverse=False)
    return transactions
