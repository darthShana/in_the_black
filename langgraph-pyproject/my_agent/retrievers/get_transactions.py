import json
from datetime import datetime
from typing import List, Optional

import decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr

from my_agent.model.transaction import Transaction

dynamodb = boto3.resource('dynamodb')


def to_transaction(i):
    return Transaction(
        transaction_id=i['TransactionID'],
        date=datetime.strptime(i['TransactionDate'], '%Y/%m/%d'),
        transaction_type=i['TransactionType'],
        amount=decimal.Decimal(i['TransactionAmount']),
        custom_id=i['CustomID'],
        bank_account_type=json.loads(i['BankAccountType'])
    )


def get_transactions(user_id: str, start: Optional[datetime], end: Optional[datetime]) -> List[Transaction]:
    table = dynamodb.Table('Transactions')

    customer_attr = Attr('CustomerNumber')
    filter_expression = customer_attr.eq(user_id)

    if start is not None or end is not None:
        date_attr = Attr('TransactionDate')

        if start is not None and end is not None:
            filter_expression &= date_attr.between(start.strftime('%Y/%m/%d'), end.strftime('%Y/%m/%d'))
        elif start is not None:
            filter_expression &= date_attr.gte(start.strftime('%Y/%m/%d'))
        elif end is not None:
            filter_expression &= date_attr.lte(end.strftime('%Y/%m/%d'))

    response = table.scan(
        FilterExpression=filter_expression
    )

    transactions = [to_transaction(i) for i in response['Items']]
    transactions.sort(key=lambda t: t.date, reverse=False)
    return transactions
