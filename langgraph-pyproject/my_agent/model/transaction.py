from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic.v1 import BaseModel, Field


available_transaction_types = [{
        "name": "loan interest",
        "description": "interest payments on loans (mortgages) used for the rental properties"
    }, {
        "name": "rental income",
        "description": "rental income received from rental properties"
    }, {
        "name": "water",
        "description": "payments made for water"
    }, {
        "name": "water refund",
        "description": "a deposit made as refund for water"
    }, {
       "name": "rates",
       "description": "payments made for council rates"
    }, {
       "name": "insurance",
       "description": "payments made for proprietary insurance"
    }, {
        "name": "property management",
        "description": "property management fees paid"
    }, {
        "name": "property maintenance",
        "description": "expenses for property maintenance"
    }, {
        "name": "capital withdrawal",
        "description": "funds taken out of the company account"
    }, {
        "name": "capital deposit",
        "description": "funds put into the company account"
    }, {
        "name": "capital deposit reversal",
        "description": "a reversal of funds put into the company account"
    }, {
        "name": "unknown payment",
        "description": "other payments made from this bank account"
    }, {
        "name": "unknown deposit",
        "description": "other deposits made to this bank account"
    }]


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