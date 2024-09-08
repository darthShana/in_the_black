import logging
from langsmith import unit
from unittest.mock import ANY

from my_agent.model.transaction import BankAccountTypeEnum
from my_agent.tools.process_statement import classify_statement_transactions
from my_agent.tools.save_transactions import to_dynamo_items

log = logging.getLogger(__name__)

customer_number = 'b5c7f883-eb98-4ef0-a744-1496510552c2'


@unit
def test_to_dynamo_item():
    trans = {"Date": "2023/04/01", "Unique Id": "2023040101", "Tran Type": "LOAN INT", "Cheque Number": "", "Payee": "LOAN - INTEREST", "Memo": "12-3273-0018314-92 001 INTEREST", "Amount":-796.92}
    classified = {"Unique Id": "2023040101", "transaction_type": "loan interest"}

    mapped_item = to_dynamo_items(customer_number, [trans | classified], BankAccountTypeEnum.COMPANY_ACCOUNT)[0]

    expected_item = {
        'TransactionID': {'S': ANY},
        'CustomerNumber': {'S': customer_number},
        'TransactionDate': {'S': "2023/04/01"},
        'TransactionType': {'S': "loan interest"},
        'TransactionAmount': {'S': "-796.92"},
        'BankAccountType': {'S': '"company_account"'},
        'CustomID': {'S': "2023040101"},
        'content': {'S': str({
            "Date": "2023/04/01", "Unique Id": "2023040101", "Tran Type": "LOAN INT", "Cheque Number": "", "Payee": "LOAN - INTEREST", "Memo": "12-3273-0018314-92 001 INTEREST", "Amount": -796.92, 'transaction_type': 'loan interest'
        })}
    }

    assert mapped_item == expected_item


@unit
def test_normalise_date_format():
    trans = {
        "Date": "31/03/2024", "Details": "Loan Payment", "Amount": 1496.83, "PrincipalBalance": 555217.82
    }
    classified = {"Unique Id": "31032024", "transaction_type": "capital deposit"}

    mapped_item = to_dynamo_items(customer_number, [trans | classified], BankAccountTypeEnum.COMPANY_ACCOUNT)[0]

    expected_item = {
        'TransactionID': {'S': ANY},
        'CustomerNumber': {'S': customer_number},
        'TransactionDate': {'S': "2024/03/31"},
        'TransactionType': {'S': "capital deposit"},
        'TransactionAmount': {'S': "1496.83"},
        'BankAccountType': {'S': '"company_account"'},
        'CustomID': {'S': "31032024"},
        'content': {'S': str({
            "Date": "31/03/2024", "Details": "Loan Payment", "Amount": 1496.83, "PrincipalBalance": 555217.82, "Unique Id": "31032024", 'transaction_type': 'capital deposit'
        })}
    }

    assert mapped_item == expected_item



