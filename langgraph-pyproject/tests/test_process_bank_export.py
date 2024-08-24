import datetime
import logging
from langsmith import unit
from unittest.mock import ANY

from my_agent.model.transaction import BankAccountTypeEnum
from my_agent.retrievers.get_transactions import get_transactions
from my_agent.tools.process_bank_export import to_dynamo_items

log = logging.getLogger(__name__)

customer_number = 'b5c7f883-eb98-4ef0-a744-1496510552c2'


@unit
def test_process_bank_export(upload_transactions: bool, transaction_filter):

    transactions = get_transactions(customer_number, datetime.datetime(2023, 4, 1), datetime.datetime(2024,4, 1))
    assert len(transactions) == 27 + 25
    assert transactions[0].date == datetime.datetime(2023, 4, 1)
    assert transactions[-1].date == datetime.datetime(2024, 3, 28)


@unit
def test_to_dynamo_item():
    trans = {"Date": "2023/04/01", "Unique Id": "2023040101", "Tran Type": "LOAN INT", "Cheque Number": "", "Payee": "LOAN - INTEREST", "Memo": "12-3273-0018314-92 001 INTEREST", "Amount":-796.92}
    classified = {"Unique Id": "2023040101", "transaction_type": "loan_interest"}

    mapped_item = to_dynamo_items(customer_number, [trans | classified], BankAccountTypeEnum.COMPANY_ACCOUNT)[0]

    expected_item = {
        'TransactionID': {'S': ANY},
        'CustomerNumber': {'S': customer_number},
        'TransactionDate': {'S': "2023/04/01"},
        'TransactionType': {'S': "loan_interest"},
        'TransactionAmount': {'S': "-796.92"},
        'BankAccountType': {'S': '"company_account"'},
        'CustomID': {'S': "2023040101"},
        'content': {'S': str({
            "Date": "2023/04/01", "Unique Id": "2023040101", "Tran Type": "LOAN INT", "Cheque Number": "", "Payee": "LOAN - INTEREST", "Memo": "12-3273-0018314-92 001 INTEREST", "Amount": -796.92, 'transaction_type': 'loan_interest'
        })}
    }

    assert mapped_item == expected_item



