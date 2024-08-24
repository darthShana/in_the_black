import json
import logging
from typing import List, Dict, Annotated

from langchain_core.tools import StructuredTool
from langgraph.prebuilt import InjectedState
from pydantic.v1 import BaseModel, Field

from my_agent.model.account import Account, AccountTypeEnum
from my_agent.model.chart_of_accounts import ChartOfAccounts, default_chart_of_accounts
from my_agent.model.transaction import Transaction, BankAccountTypeEnum
log = logging.getLogger(__name__)


class GetAccountsInput(BaseModel):
    state: Annotated[dict, InjectedState] = Field(description="current state")
    chart_of_accounts: ChartOfAccounts = Field(description="a json object specifies which accounts to debit and credit for each transaction type")


def get_accounts(state: Annotated[dict, InjectedState], chart_of_accounts: ChartOfAccounts) -> Dict[str, Account]:
    accounts: Dict[str, Account] = {}
    transactions = json.loads(state['transactions'])['bank_transactions']

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
        Useful to calculate the accounts for a set of transactions
        """,
    args_schema=GetAccountsInput,
)


def get_chart_of_accounts() -> ChartOfAccounts:
    return default_chart_of_accounts


get_chart_of_accounts_tool_name = "get_chart_of_accounts"
get_chart_of_accounts_tool = StructuredTool.from_function(
    func=get_chart_of_accounts,
    name=get_chart_of_accounts_tool_name,
    description="""
        Useful to get a chart of accounts which can be used to determine which accounts to debit and credit for each transaction
        """
)
