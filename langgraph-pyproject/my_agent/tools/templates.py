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
            "TransactionDate": "2023/04/01", "TransactionAmount" : 796.92, "transaction_type": "loan interest", "UniqueID": "2023040101"
        }"""
    }, {
        "transaction": """{
            'date': 'Mar 2024', 'account': 'Rent', 'includedTax': None, 'moneyOut': None, 'moneyIn': 3750, 'Unique Id': 'Mar2024_2', 'transaction_type': 'rental income'
        }""",
        "result": """{
            "TransactionDate": "2024/04/01", "TransactionAmount" : 3750, "transaction_type": "rental income" "UniqueID": "Mar2024_1"
        }"""
    }, {
        "transaction": """{
            'date': 'Mar 2024', 'account': 'Management fee', 'includedTax': 49.44, 'moneyOut': 379.2, 'moneyIn': None, 'Unique Id': 'Feb2024_2', 'transaction_type': 'property management'
        }""",
        "result": """{
            "TransactionDate": "2024/04/01", "TransactionAmount" : 379.2, "transaction_type": "property management" "UniqueID": "Mar2024_2"
        }"""
    }
]

expense_validation_prefix = """
Given a monthly breakdown of expenses for a renal property company, review them to find possible book keeping errors
look for anomalies in what expenses are monthly and negative/positive amounts 
"""

expense_validation_example_template = """
Here is an example:
<example>
Monthly Expenses:
{monthly_expenses}
results:
{results}
"""

expense_validation_examples = [
    {
        "monthly_expenses": """[
            {'period': 'April 2023', 'expenses': {'Management Fees': Decimal('164.32'), 'Water': Decimal('-80'), 'Mortgage Interest': Decimal('2594.99'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'May 2023', 'expenses': {'Water': Decimal('45.35'), 'Management Fees': Decimal('205.4'), 'Mortgage Interest': Decimal('2507.55'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'June 2023', 'expenses': {'Mortgage Interest': Decimal('2587.84'), 'Water': Decimal('-80'), 'Management Fees': Decimal('164.32'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'July 2023', 'expenses': {'Mortgage Interest': Decimal('2500.94'), 'Water': Decimal('-6.63'), 'Management Fees': Decimal('164.32'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'August 2023', 'expenses': {'Maintenance Expenses': Decimal('149.5'), 'Management Fees': Decimal('619.94'), 'Mortgage Interest': Decimal('2581.08'), 'Rates': Decimal('552.83'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'September 2023', 'expenses': {'Water': Decimal('-28'), 'Mortgage Interest': Decimal('2577.64'), 'Management Fees': Decimal('31.64'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'October 2023', 'expenses': {'Mortgage Interest': Decimal('2490.67'), 'Water': Decimal('30'), 'Management Fees': Decimal('88.59'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'November 2023', 'expenses': {'Management Fees': Decimal('63.27'), 'Water': Decimal('189.6'), 'Rates': Decimal('-3000'), 'Mortgage Interest': Decimal('2570.56'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'December 2023', 'expenses': {'Mortgage Interest': Decimal('2484.36'), 'Management Fees': Decimal('63.27'), 'Water': Decimal('30'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'January 2024', 'expenses': {'Water': Decimal('37'), 'Mortgage Interest': Decimal('2564.08'), 'Insurance': Decimal('162.48')}}, 
            {'period': 'February 2024', 'expenses': {'Rates': Decimal('278.4'), 'Mortgage Interest': Decimal('2559.46'), 'Management Fees': Decimal('552.83'), 'Insurance': Decimal('162.63')}}, 
            {'period': 'March 2024', 'expenses': {'Water': Decimal('134.37'), 'Mortgage Interest': Decimal('2392.0'), 'Management Fees': Decimal('110.6'), 'Insurance': Decimal('162.63')}}]
        """,
        "results": """[
            {'period': 'November 2023', 'account': 'Rates', 'issue': 'Rates for this month is a large negative amount, Its unlikely that rates would be a large refund'}
        ]"""
    },
    {
        "monthly_expenses": """[
            {'period': 'April 2023', 'expenses': {'Management Fees': Decimal('164.32'), 'Water': Decimal('-80'), 'Mortgage Interest': Decimal('2594.99'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'May 2023', 'expenses': {'Water': Decimal('45.35'), 'Management Fees': Decimal('205.4'), 'Mortgage Interest': Decimal('2507.55'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'June 2023', 'expenses': {'Mortgage Interest': Decimal('2587.84'), 'Water': Decimal('-80'), 'Management Fees': Decimal('164.32'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'July 2023', 'expenses': {'Water': Decimal('-6.63'), 'Management Fees': Decimal('164.32'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'August 2023', 'expenses': {'Maintenance Expenses': Decimal('149.5'), 'Management Fees': Decimal('619.94'), 'Mortgage Interest': Decimal('2581.08'), 'Rates': Decimal('552.83'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'September 2023', 'expenses': {'Water': Decimal('-28'), 'Mortgage Interest': Decimal('2577.64'), 'Management Fees': Decimal('31.64'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'October 2023', 'expenses': {'Mortgage Interest': Decimal('2490.67'), 'Water': Decimal('30'), 'Management Fees': Decimal('88.59'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'November 2023', 'expenses': {'Management Fees': Decimal('63.27'), 'Water': Decimal('189.6'), 'Rates': Decimal('552.83'), 'Mortgage Interest': Decimal('2570.56'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'December 2023', 'expenses': {'Mortgage Interest': Decimal('2484.36'), 'Management Fees': Decimal('63.27'), 'Water': Decimal('30'), 'Insurance': Decimal('165.61')}}, 
            {'period': 'January 2024', 'expenses': {'Water': Decimal('37'), 'Mortgage Interest': Decimal('2564.08'), 'Insurance': Decimal('162.48')}}, 
            {'period': 'February 2024', 'expenses': {'Rates': Decimal('278.4'), 'Mortgage Interest': Decimal('2559.46'), 'Management Fees': Decimal('552.83'), 'Insurance': Decimal('162.63')}}, 
            {'period': 'March 2024', 'expenses': {'Water': Decimal('134.37'), 'Mortgage Interest': Decimal('2392.0'), 'Management Fees': Decimal('110.6'), 'Insurance': Decimal('162.63')}}]
        """,
        "results": """[
            {'period': 'July 2023', 'account': 'Mortgage Interest', issue: 'This month is missing Mortgage Interest, it seems to be a monthly expense so its suspicious that its missed in one month'}
        ]"""
    }
]
