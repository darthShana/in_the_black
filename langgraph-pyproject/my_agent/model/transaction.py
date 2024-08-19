from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic.v1 import BaseModel, Field


class BankAccountTypeEnum(str, Enum):
    COMPANY_ACCOUNT = 'company_account'
    PERSONAL_ACCOUNT = 'personal_account'


class Transaction(BaseModel):
    transaction_id: str = Field(description="the transaction id")
    date: datetime = Field(description="date and time of this transaction")
    transaction_type: str = Field(description="the type of transaction")
    amount: Decimal = Field(description="the transaction amount")
    custom_id: Optional[str] = Field(description="a custom id for this transaction")
    bank_account_type: BankAccountTypeEnum = Field(description="the type of bank account this transaction came from")