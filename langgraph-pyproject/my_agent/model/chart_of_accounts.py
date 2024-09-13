from typing import Dict

from pydantic.v1 import BaseModel, Field

from my_agent.model.account import AccountTypeEnum


class ChartOfAccounts(BaseModel):
    accounts: Dict = Field(description="dictionary of account names mapped to account descriptions")
    transaction_map: Dict = Field(description="dictionary of transaction types mapped to the credit and debit account for the transaction")


default_chart_of_accounts = ChartOfAccounts(
        accounts={
            'bank_account': {'display_name': 'Bank Account', 'account_type': AccountTypeEnum.ASSET},
            'mortgage_interest': {'display_name': 'Mortgage Interest', 'account_type': AccountTypeEnum.EXPENSES},
            'rental_revenue': {'display_name': 'Rental Revenue', 'account_type': AccountTypeEnum.REVENUE},
            'capital': {'display_name': 'Capital', 'account_type': AccountTypeEnum.EQUITY},
            'water': {'display_name': 'Water', 'account_type': AccountTypeEnum.EXPENSES},
            'rates': {'display_name': 'Rates', 'account_type': AccountTypeEnum.EXPENSES},
            'insurance': {'display_name': 'Insurance', 'account_type': AccountTypeEnum.EXPENSES},
            'loans': {'display_name': 'loans', 'account_type': AccountTypeEnum.LIABILITY},
            'management_fees': {'display_name': 'Management Fees', 'account_type': AccountTypeEnum.EXPENSES},
            'maintenance_expenses': {'display_name': 'Maintenance Expenses', 'account_type': AccountTypeEnum.EXPENSES}
        },
        transaction_map={
            'loan interest': {'debit': 'mortgage_interest', 'credit': 'bank_account'},
            'rental income': {'debit': 'bank_account', 'credit': 'rental_revenue'},
            'water': {'debit': 'water', 'credit': 'bank_account'},
            'water refund': {'debit': 'bank_account', 'credit': 'water'},
            'rates': {'debit': 'rates', 'credit': 'bank_account'},
            'insurance': {'debit': 'insurance', 'credit': 'bank_account'},
            'property management': {'debit': 'management_fees', 'credit': 'bank_account'},
            'property maintenance': {'debit': 'maintenance_expenses', 'credit': 'bank_account'},
            'capital withdrawal':  {'debit': 'capital', 'credit': 'bank_account'},
            'capital deposit':  {'debit': 'bank_account', 'credit': 'capital'},
            'capital deposit reversal':  {'debit': 'capital', 'credit': 'bank_account'},
            'loan deposit':  {'debit': 'bank_account', 'credit': 'loans'}
        }
    )