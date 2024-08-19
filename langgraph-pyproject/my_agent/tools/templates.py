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
            "Date": "2023/04/01", "Unique Id": "2023040101", "Tran Type": "LOAN INT", "Cheque Number": "", "Payee": "LOAN - INTEREST", "Memo": "12-3273-0018314-92 001 INTEREST", "Amount":-796.92
        }""",
        "result": """{
            "TransactionDate": "2023/04/01", "TransactionAmount" : -796.92, "": "CustomID": "2023040101"
        }"""
    }
]
