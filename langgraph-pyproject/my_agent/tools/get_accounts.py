import logging
from datetime import datetime
from typing import Dict

from langchain_core.tools import StructuredTool
from pydantic.v1 import BaseModel, Field

from my_agent.model.account import Account, AccountTypeEnum
from my_agent.model.chart_of_accounts import default_chart_of_accounts
from my_agent.model.transaction import BankAccountTypeEnum
from my_agent.retrievers.get_user import UserRetriever
from my_agent.retrievers.get_transactions import get_transactions

log = logging.getLogger(__name__)


class GetAccountsInput(BaseModel):
    start: datetime = Field(description="get transactions after this date and time")
    end: datetime = Field(description="get transactions before this date and time")


def get_accounts(start: datetime, end: datetime) -> Dict[str, Account]:
    accounts: Dict[str, Account] = {}
    user = UserRetriever.get_user("in here test")
    chart_of_accounts = default_chart_of_accounts

    transactions = get_transactions(user.user_id, start, end)

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

        if (accounts[credit_account_name].account_type in [AccountTypeEnum.ASSET, AccountTypeEnum.EQUITY, AccountTypeEnum.LIABILITY] and
                transaction.amount < 0):
            transaction.amount = -transaction.amount

        # Add debit transaction
        accounts[debit_account_name].debit(transaction)

        # Add credit transaction
        accounts[credit_account_name].credit(transaction)

    return accounts


get_accounts_tool_name = "get_accounts"
get_accounts_tool = StructuredTool.from_function(
    func=get_accounts,
    name=get_accounts_tool_name,
    description="""
        Useful to calculate the accounts for time period
        """,
    args_schema=GetAccountsInput
)

