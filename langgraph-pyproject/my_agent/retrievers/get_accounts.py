import logging
from datetime import datetime
from typing import Dict
from dateutil.relativedelta import relativedelta

from my_agent.model.account import Account, AccountTypeEnum
from my_agent.model.chart_of_accounts import default_chart_of_accounts
from my_agent.model.transaction import BankAccountTypeEnum
from my_agent.model.user import UserInfo
from my_agent.retrievers.get_transactions import get_transactions

log = logging.getLogger(__name__)


def monthly_expenses(user: UserInfo, current_date, end_date):
    monthly = []
    while current_date <= end_date:
        last_day = (current_date + relativedelta(months=1, days=-1)).day
        accounts = get_accounts(user, current_date, current_date.replace(day=last_day))
        month = {
            'period': current_date.strftime('%B %Y'),
            'expenses': {account.display_name: float(account.balance()) for account in accounts.values() if account.account_type == AccountTypeEnum.EXPENSES}
        }
        monthly.append(month)
        current_date += relativedelta(months=1)

    return monthly


def get_accounts(user: UserInfo, start: datetime, end: datetime) -> Dict[str, Account]:
    accounts: Dict[str, Account] = {}
    chart_of_accounts = default_chart_of_accounts

    transactions = get_transactions(user.user_id, start, end)
    log.info(f"Retrieved transactions:{len(transactions)}")

    for transaction in transactions:
        transaction_type = transaction.transaction_type

        if transaction_type in chart_of_accounts.transaction_map:
            debit_account_name = chart_of_accounts.transaction_map[transaction_type]['debit']
            credit_account_name = chart_of_accounts.transaction_map[transaction_type]['credit']
        else:
            raise Exception(f"Error: Unknown transaction type '{transaction_type}'")

        if transaction.bank_account_type == BankAccountTypeEnum.PERSONAL_ACCOUNT:
            debit_account_name = 'capital' if debit_account_name == 'bank_account' else debit_account_name
            credit_account_name = 'capital' if credit_account_name == 'bank_account' else credit_account_name

        # Ensure accounts exist
        if debit_account_name not in accounts:
            debit_account = chart_of_accounts.accounts[debit_account_name]
            accounts[debit_account_name] = Account(
                display_name=debit_account['display_name'],
                account_type=debit_account['account_type']
            )
        if credit_account_name not in accounts:
            credit_account = chart_of_accounts.accounts[credit_account_name]
            accounts[credit_account_name] = Account(
                display_name=credit_account['display_name'],
                account_type=credit_account['account_type']
            )

        # Add debit transaction
        accounts[debit_account_name].debit(transaction)

        # Add credit transaction
        accounts[credit_account_name].credit(transaction)

    return accounts
