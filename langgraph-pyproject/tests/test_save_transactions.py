import ast
import json
import logging
from unittest.mock import ANY

from langchain_core.utils.json import parse_json_markdown
from langsmith import unit

from my_agent.model.account import Account
from my_agent.model.transaction import BankAccountTypeEnum
from my_agent.retrievers.transaction_retriever import TransactionRetriever
from my_agent.tools.save_transactions import to_dynamo_items

customer_number = 'b5c7f883-eb98-4ef0-a744-1496510552c2'
log = logging.getLogger(__name__)


@unit
def test_save_transactions():
    transactions = [
        {'date': 'Aug 2023', 'description': 'Council rates', 'includedTax': None, 'moneyOut': 552.83, 'moneyIn': None, 'Unique Id': 'Aug202301', 'transaction_type': 'rates'},
        {"Date": "2023/04/01", "Unique Id": "2023040101", "Tran Type": "LOAN INT", "Cheque Number": "", "Payee": "LOAN - INTEREST", "Memo": "12-3273-0018314-92 001 INTEREST", "Amount": -796.92, 'transaction_type': 'loan interest'},
        {'date': 'Mar 2024', 'account': 'Rent', 'includedTax': None, 'moneyOut': None, 'moneyIn': 3750, 'Unique Id': 'Mar2024_2', 'transaction_type': 'rental income'}
    ]

    to_save = to_dynamo_items('123', transactions, BankAccountTypeEnum.PERSONAL_ACCOUNT)

    assert to_save[0]['TransactionAmount']['S'] == "552.83"
    assert to_save[0]['TransactionDate']['S'] == '2023/08/01'

    assert to_save[1]['TransactionAmount']['S'] == "796.92"
    assert to_save[1]['TransactionDate']['S'] == '2023/04/01'

    assert to_save[2]['TransactionAmount']['S'] == "3750"
    assert to_save[2]['TransactionDate']['S'] == '2024/03/01'


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
        'TransactionAmount': {'S': "796.92"},
        'BankAccountType': {'S': '"company account"'},
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
        'BankAccountType': {'S': '"company account"'},
        'CustomID': {'S': "31032024"},
        'content': {'S': str({
            "Date": "31/03/2024", "Details": "Loan Payment", "Amount": 1496.83, "PrincipalBalance": 555217.82, "Unique Id": "31032024", 'transaction_type': 'capital deposit'
        })}
    }

    assert mapped_item == expected_item


@unit
def test_large_transaction_file_transform():
    json_str = """
    Here is the extracted list of transactions in JSON format:\n\n```json\n[\n  {\n    "date": "Apr 2023",\n    "description": "Management fee",\n    "includedTax": 21.44,\n    "moneyOut": 164.32,\n    "moneyIn": 0\n  },\n  {\n    "date": "Apr 2023",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 2600.00\n  },\n  {\n    "date": "Apr 2023",\n    "description": "Water usage",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 80.00\n  },\n  {\n    "date": "May 2023",\n    "description": "Management fee",\n    "includedTax": 26.80,\n    "moneyOut": 205.40,\n    "moneyIn": 0\n  },\n  {\n    "date": "May 2023",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 3250.00\n  },\n  {\n    "date": "May 2023",\n    "description": "Water rates",\n    "includedTax": 0,\n    "moneyOut": 248.50,\n    "moneyIn": 0\n  },\n  {\n    "date": "May 2023",\n    "description": "Water usage",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 203.15\n  },\n  {\n    "date": "Jun 2023",\n    "description": "Management fee",\n    "includedTax": 21.44,\n    "moneyOut": 164.32,\n    "moneyIn": 0\n  },\n  {\n    "date": "Jun 2023",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 2600.00\n  },\n  {\n    "date": "Jun 2023",\n    "description": "Water usage",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 80.00\n  },\n  {\n    "date": "Jul 2023",\n    "description": "Management fee",\n    "includedTax": 21.44,\n    "moneyOut": 164.32,\n    "moneyIn": 0\n  },\n  {\n    "date": "Jul 2023",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 2600.00\n  },\n  {\n    "date": "Jul 2023",\n    "description": "Water rates",\n    "includedTax": 0,\n    "moneyOut": 173.37,\n    "moneyIn": 0\n  },\n  {\n    "date": "Jul 2023",\n    "description": "Water usage",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 180.00\n  },\n  {\n    "date": "Aug 2023",\n    "description": "Council rates",\n    "includedTax": 0,\n    "moneyOut": 552.83,\n    "moneyIn": 0\n  },\n  {\n    "date": "Aug 2023",\n    "description": "Letting fee",\n    "includedTax": 56.25,\n    "moneyOut": 431.25,\n    "moneyIn": 0\n  },\n  {\n    "date": "Aug 2023",\n    "description": "Management fee",\n    "includedTax": 24.61,\n    "moneyOut": 188.69,\n    "moneyIn": 0\n  },\n  {\n    "date": "Aug 2023",\n    "description": "Plumbing",\n    "includedTax": 19.50,\n    "moneyOut": 149.50,\n    "moneyIn": 0\n  },\n  {\n    "date": "Aug 2023",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 2985.71\n  },\n  {\n    "date": "Aug 2023",\n    "description": "Water rates",\n    "includedTax": 0,\n    "moneyOut": 87.48,\n    "moneyIn": 0\n  },\n  {\n    "date": "Aug 2023",\n    "description": "Water usage",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 257.35\n  },\n  {\n    "date": "Sep 2023",\n    "description": "Management fee",\n    "includedTax": 24.72,\n    "moneyOut": 189.60,\n    "moneyIn": 0\n  },\n  {\n    "date": "Sep 2023",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 3000.00\n  },\n  {\n    "date": "Sep 2023",\n    "description": "Water rates",\n    "includedTax": 0,\n    "moneyOut": 31.64,\n    "moneyIn": 0\n  },\n  {\n    "date": "Oct 2023",\n    "description": "Management fee",\n    "includedTax": 24.72,\n    "moneyOut": 189.60,\n    "moneyIn": 0\n  },\n  {\n    "date": "Oct 2023",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 3000.00\n  },\n  {\n    "date": "Oct 2023",\n    "description": "Water rates",\n    "includedTax": 0,\n    "moneyOut": 88.59,\n    "moneyIn": 0\n  },\n  {\n    "date": "Nov 2023",\n    "description": "Council rates",\n    "includedTax": 0,\n    "moneyOut": 552.83,\n    "moneyIn": 0\n  },\n  {\n    "date": "Nov 2023",\n    "description": "Management fee",\n    "includedTax": 24.72,\n    "moneyOut": 189.60,\n    "moneyIn": 0\n  },\n  {\n    "date": "Nov 2023",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 3000.00\n  },\n  {\n    "date": "Nov 2023",\n    "description": "Water rates",\n    "includedTax": 0,\n    "moneyOut": 63.27,\n    "moneyIn": 0\n  },\n  {\n    "date": "Dec 2023",\n    "description": "Management fee",\n    "includedTax": 24.72,\n    "moneyOut": 189.60,\n    "moneyIn": 0\n  },\n  {\n    "date": "Dec 2023",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 3000.00\n  },\n  {\n    "date": "Dec 2023",\n    "description": "Water rates",\n    "includedTax": 0,\n    "moneyOut": 63.27,\n    "moneyIn": 0\n  },\n  {\n    "date": "Jan 2024",\n    "description": "Management fee",\n    "includedTax": 6.18,\n    "moneyOut": 47.40,\n    "moneyIn": 0\n  },\n  {\n    "date": "Jan 2024",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 3750.00\n  },\n  {\n    "date": "Feb 2024",\n    "description": "Council rates",\n    "includedTax": 0,\n    "moneyOut": 552.83,\n    "moneyIn": 0\n  },\n  {\n    "date": "Feb 2024",\n    "description": "Management fee",\n    "includedTax": 49.44,\n    "moneyOut": 379.20,\n    "moneyIn": 0\n  },\n  {\n    "date": "Feb 2024",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 3000.00\n  },\n  {\n    "date": "Feb 2024",\n    "description": "Water rates",\n    "includedTax": 0,\n    "moneyOut": 75.92,\n    "moneyIn": 0\n  },\n  {\n    "date": "Feb 2024",\n    "description": "Water usage",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 278.40\n  },\n  {\n    "date": "Mar 2024",\n    "description": "Management fee",\n    "includedTax": 14.42,\n    "moneyOut": 110.60,\n    "moneyIn": 0\n  },\n  {\n    "date": "Mar 2024",\n    "description": "Rent",\n    "includedTax": 0,\n    "moneyOut": 0,\n    "moneyIn": 3750.00\n  },\n  {\n    "date": "Mar 2024",\n    "description": "Water rates",\n    "includedTax": 0,\n    "moneyOut": 134.37,\n    "moneyIn": 0\n  }\n]\n```
    """
    to_classify = parse_json_markdown(json_str)

    result_str = """
    [{'Unique Id': 'Apr2023-01', 'transaction_type': 'property management'}, {'Unique Id': 'Apr2023-02', 'transaction_type': 'rental income'}, {'Unique Id': 'Apr2023-03', 'transaction_type': 'water refund'}, {'Unique Id': 'May2023-01', 'transaction_type': 'property management'}, {'Unique Id': 'May2023-02', 'transaction_type': 'rental income'}, {'Unique Id': 'May2023-03', 'transaction_type': 'water'}, {'Unique Id': 'May2023-04', 'transaction_type': 'water refund'}, {'Unique Id': 'Jun2023-01', 'transaction_type': 'property management'}, {'Unique Id': 'Jun2023-02', 'transaction_type': 'rental income'}, {'Unique Id': 'Jun2023-03', 'transaction_type': 'water refund'}, {'Unique Id': 'Jul2023-01', 'transaction_type': 'property management'}, {'Unique Id': 'Jul2023-02', 'transaction_type': 'rental income'}, {'Unique Id': 'Jul2023-03', 'transaction_type': 'water'}, {'Unique Id': 'Jul2023-04', 'transaction_type': 'water refund'}, {'Unique Id': 'Aug2023-01', 'transaction_type': 'rates'}, {'Unique Id': 'Aug2023-02', 'transaction_type': 'property management'}, {'Unique Id': 'Aug2023-03', 'transaction_type': 'property management'}, {'Unique Id': 'Aug2023-04', 'transaction_type': 'property maintenance'}, {'Unique Id': 'Aug2023-05', 'transaction_type': 'rental income'}, {'Unique Id': 'Aug2023-06', 'transaction_type': 'water'}, {'Unique Id': 'Aug2023-07', 'transaction_type': 'water refund'}, {'Unique Id': 'Sep2023-01', 'transaction_type': 'property management'}, {'Unique Id': 'Sep2023-02', 'transaction_type': 'rental income'}, {'Unique Id': 'Sep2023-03', 'transaction_type': 'water'}, {'Unique Id': 'Oct2023-01', 'transaction_type': 'property management'}, {'Unique Id': 'Oct2023-02', 'transaction_type': 'rental income'}, {'Unique Id': 'Oct2023-03', 'transaction_type': 'water'}, {'Unique Id': 'Nov2023-01', 'transaction_type': 'rates'}, {'Unique Id': 'Nov2023-02', 'transaction_type': 'property management'}, {'Unique Id': 'Nov2023-03', 'transaction_type': 'rental income'}, {'Unique Id': 'Nov2023-04', 'transaction_type': 'water'}, {'Unique Id': 'Dec2023-01', 'transaction_type': 'property management'}, {'Unique Id': 'Dec2023-02', 'transaction_type': 'rental income'}, {'Unique Id': 'Dec2023-03', 'transaction_type': 'water'}, {'Unique Id': 'Jan2024-01', 'transaction_type': 'property management'}, {'Unique Id': 'Jan2024-02', 'transaction_type': 'rental income'}, {'Unique Id': 'Feb2024-01', 'transaction_type': 'rates'}, {'Unique Id': 'Feb2024-02', 'transaction_type': 'property management'}, {'Unique Id': 'Feb2024-03', 'transaction_type': 'rental income'}, {'Unique Id': 'Feb2024-04', 'transaction_type': 'water'}, {'Unique Id': 'Feb2024-05', 'transaction_type': 'water refund'}, {'Unique Id': 'Mar2024-01', 'transaction_type': 'property management'}, {'Unique Id': 'Mar2024-02', 'transaction_type': 'rental income'}, {'Unique Id': 'Mar2024-03', 'transaction_type': 'water'}]
    """
    result_str = result_str.strip()
    transaction_results = ast.literal_eval(result_str)

    assert len(to_classify) == len(transaction_results)

    to_map = [transaction | transaction_type for transaction, transaction_type in zip(to_classify, transaction_results)]
    mapped_items = to_dynamo_items(customer_number, to_map, BankAccountTypeEnum.COMPANY_ACCOUNT)

    assert len(mapped_items) == len(to_map)
    assert mapped_items[-1]['TransactionType']['S'] == to_map[-1]['transaction_type']
