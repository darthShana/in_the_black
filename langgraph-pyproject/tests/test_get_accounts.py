import logging
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from langsmith import unit

from my_agent.model.transaction import Transaction, BankAccountTypeEnum

from my_agent.tools.get_accounts import get_accounts

log = logging.getLogger(__name__)


def to_transaction(row, transaction_type):
    return Transaction(
        transaction_id=str(uuid.uuid4()),
        date=datetime.strptime(row['Date'], '%Y/%m/%d'),
        transaction_type=transaction_type['transaction_type'],
        amount=row['Amount'],
        custom_id=row['Unique Id'],
        bank_account_type=BankAccountTypeEnum.COMPANY_ACCOUNT
    )


def to_overrides(transactions: list[Transaction], overrides):
    ret = {}
    for override in overrides:
        transaction_id = next(t.transaction_id for t in transactions if t.custom_id == str(override['transaction_id']))
        ret[transaction_id] = {
            'debit': override['debit'],
            'credit': override['credit'],
        }
    return ret


@unit
def test_get_accounts(sample_transaction_file, sample_transaction_types, sample_transaction_overrides, chart_of_accounts, monkeypatch):
    transactions = [to_transaction(row, transaction_type) for row, transaction_type in zip(
        sample_transaction_file.to_dict('records'),
        sample_transaction_types.to_dict('records'))]

    transactions = [transaction for transaction in transactions if datetime(2023, 4, 1) <= transaction.date <= datetime(2024, 3, 31)]
    monkeypatch.setattr('my_agent.tools.get_accounts.get_transactions', lambda user_id, start, end: transactions)

    accounts = get_accounts(datetime(2023, 4, 1), datetime(2024, 3, 31))

    assert accounts['bank_account'].display_name == "Bank Account"
    assert len(accounts['bank_account'].transactions()) == 27
    assert accounts['bank_account'].balance() == Decimal('6369.13')

    assert accounts['mortgage_interest'].display_name == "Mortgage Interest"
    assert len(accounts['mortgage_interest'].transactions()) == 12
    assert accounts['mortgage_interest'].balance() == Decimal('20639.56')

    assert accounts['capital'].display_name == "Capital"
    assert len(accounts['capital'].transactions()) == 3
    assert accounts['capital'].balance() == Decimal('-8450.00')


def test_get_accounts_expense(chart_of_accounts, monkeypatch):
    transactions = [Transaction(
        transaction_id=str(uuid.uuid4()),
        date=datetime.strptime('2024/02/20', '%Y/%m/%d'),
        transaction_type='water',
        amount=-45,
        custom_id='2345',
        bank_account_type=BankAccountTypeEnum.PERSONAL_ACCOUNT
    )]
    monkeypatch.setattr('my_agent.tools.get_accounts.get_transactions', lambda user_id, start, end: transactions)

    accounts = get_accounts(datetime(2023, 4, 1), datetime(2024, 3, 31))
    assert 'bank_account' not in accounts
    assert accounts['water'].balance() == Decimal('45')
    assert accounts['capital'].balance() == Decimal('45')

    transactions = [Transaction(
        transaction_id=str(uuid.uuid4()),
        date=datetime.strptime('2024/01/20', '%Y/%m/%d'),
        transaction_type='water',
        amount=-45,
        custom_id='2345',
        bank_account_type=BankAccountTypeEnum.COMPANY_ACCOUNT
    )]
    monkeypatch.setattr('my_agent.tools.get_accounts.get_transactions', lambda user_id, start, end: transactions)

    accounts = get_accounts(datetime(2023, 4, 1), datetime(2024, 3, 31))
    assert 'capital' not in accounts
    assert accounts['water'].balance() == Decimal('45.00')
    assert accounts['bank_account'].balance() == Decimal('-45.00')


def test_get_accounts_liability(chart_of_accounts, monkeypatch):
    transaction_id = str(uuid.uuid4())
    transactions = [Transaction(
        transaction_id=transaction_id,
        date=datetime.strptime('2024/02/20', '%Y/%m/%d'),
        transaction_type='loan deposit',
        amount=45,
        custom_id='2345',
        bank_account_type=BankAccountTypeEnum.COMPANY_ACCOUNT
    )]
    monkeypatch.setattr('my_agent.tools.get_accounts.get_transactions', lambda user_id, start, end: transactions)

    accounts = get_accounts(datetime(2023, 4, 1), datetime(2024, 3, 31))
    assert accounts['bank_account'].balance() == Decimal('45')
    assert accounts['loans'].balance() == Decimal('45')


def test_get_accounts_equity_investment(chart_of_accounts, monkeypatch):
    transaction_id = str(uuid.uuid4())
    transactions = [Transaction(
        transaction_id=transaction_id,
        date=datetime.strptime('2024/02/20', '%Y/%m/%d'),
        transaction_type='capital deposit',
        amount=45,
        custom_id='2345',
        bank_account_type=BankAccountTypeEnum.COMPANY_ACCOUNT
    )]
    monkeypatch.setattr('my_agent.tools.get_accounts.get_transactions', lambda user_id, start, end: transactions)

    accounts = get_accounts(datetime(2023, 4, 1), datetime(2024, 3, 31))
    assert accounts['bank_account'].balance() == Decimal('45')
    assert accounts['capital'].balance() == Decimal('45')
