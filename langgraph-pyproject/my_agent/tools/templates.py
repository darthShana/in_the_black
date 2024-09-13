dto_mapping_prefix = """
Given a list of bank transactions extract the following mandatory values
Mandatory Values:
{{mandatory_values}} 
"""

dto_mapping_example_template = """
Here is an example:
<example>
Transactions:
{transaction}
result:
{result}
"""

dto_mapping_examples = [
    {
        "transaction": """{
            "Date": "2023/04/01", "Unique Id": "2023040101", "Tran Type": "LOAN INT", "Cheque Number": "", "Payee": "LOAN - INTEREST", "Memo": "12-3273-0018314-92 001 INTEREST", "Amount":-796.92, 'transaction_type': 'loan interest'
        }""",
        "result": """{
            "TransactionDate": "2023/04/01", "TransactionAmount" : 796.92, "transaction_type": "loan interest", "CustomID": "2023040101"
        }"""
    }, {
        "transaction": """{
            'date': 'Mar 2024', 'account': 'Rent', 'includedTax': None, 'moneyOut': None, 'moneyIn': 3750, 'Unique Id': 'Mar2024_2', 'transaction_type': 'rental income'
        }""",
        "result": """{
            "TransactionDate": "2024/04/01", "TransactionAmount" : 3750, "transaction_type": "rental income" "CustomID": "Mar2024_1"
        }"""
    }, {
        "transaction": """{
            'date': 'Mar 2024', 'account': 'Management fee', 'includedTax': 49.44, 'moneyOut': 379.2, 'moneyIn': None, 'Unique Id': 'Feb2024_2', 'transaction_type': 'property management'
        }""",
        "result": """{
            "TransactionDate": "2024/04/01", "TransactionAmount" : 379.2, "transaction_type": "property management" "CustomID": "Mar2024_2"
        }"""
    }
]
