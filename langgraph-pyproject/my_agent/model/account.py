import logging
import pprint
from enum import Enum
from typing import List

from pydantic.v1 import BaseModel, Field

from my_agent.model.transaction import Transaction
log = logging.getLogger(__name__)


class AccountTypeEnum(str, Enum):
    ASSET = 'asset'
    LIABILITY = 'liability'
    EQUITY = 'equity'
    REVENUE = 'revenue'
    EXPENSES = 'expenses'


class Account(BaseModel):

    display_name: str = Field(description="pretty display name of this account")
    account_type: AccountTypeEnum = Field(description="account type, one of asset, expense, liability, sale")
    debits: List[Transaction] = Field(description="list of debits", default=[])
    credits: List[Transaction] = Field(description="list of credits", default=[])

    def debit(self, transaction: Transaction):
        self.debits.append(transaction)

    def credit(self, transaction: Transaction):
        # log.info(self.display_name)
        # log.info(self.account_type)
        # log.info(transaction.amount)
        self.credits.append(transaction)

    def transactions(self):
        return self.debits + self.credits

    def balance(self) -> float:
        debit_total = sum(transaction.amount for transaction in self.debits)
        credit_total = sum(transaction.amount for transaction in self.credits)

        if self.account_type in [AccountTypeEnum.REVENUE, AccountTypeEnum.EQUITY, AccountTypeEnum.LIABILITY]:
            return credit_total - debit_total
        else:
            return debit_total - credit_total

