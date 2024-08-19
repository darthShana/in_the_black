import logging
from typing import List, Dict

from my_agent.model.account import Account, AccountTypeEnum
from my_agent.model.chart_of_accounts import ChartOfAccounts
from my_agent.model.transaction import Transaction, BankAccountTypeEnum
log = logging.getLogger(__name__)


def get_accounts(transactions: List[Transaction], chart_of_accounts: ChartOfAccounts, overrides: dict) -> Dict[str, Account]:
    accounts: Dict[str, Account] = {}

    for transaction in transactions:
        transaction_type = transaction.transaction_type

        if transaction.transaction_id in overrides:
            debit_account_name = overrides[transaction.transaction_id]['debit']
            credit_account_name = overrides[transaction.transaction_id]['credit']
        elif transaction_type in chart_of_accounts.transaction_map:
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

        if (accounts[credit_account_name].account_type in [AccountTypeEnum.ASSET, AccountTypeEnum.EQUITY, AccountTypeEnum.LIABILITY] and
                transaction.amount < 0):
            transaction.amount = -transaction.amount

        # Add debit transaction
        accounts[debit_account_name].debit(transaction)

        # Add credit transaction
        accounts[credit_account_name].credit(transaction)

    return accounts

