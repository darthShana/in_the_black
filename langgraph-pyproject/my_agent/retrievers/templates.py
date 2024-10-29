transaction_classification_prefix = """
Given the following list of transactions for a residential property investment company. Classify each transaction
to one of the available transaction types bellow for book keeping purposes. 
Positive amounts are deposits such as revenue or cash from capital or loans.
Negative amounts are payments for expenses or withdrawals of funds.

Available Transaction Types:
{{transaction_types}}
"""

transaction_classification_example_template = """
Here is an example:
<example>
Transaction:
{transaction}
result:
{result}
"""

transaction_classification_examples = [
    {
        "transaction": """
        {
            "date": "2023/04/01", "id": "2023040101", "transaction_type": "LOAN INT", "payee": "LOAN - INTEREST", "memo": "12-3273-0018314-92 001 INTEREST", "amount": "-796.92"
        }
        """,
        "result": """
        {
            "Unique Id": "2023040101", "transaction_type": "loan interest"
        }
        """
    }, {
        "transaction": """
        {
            "date": "2023/04/28", "id": "2023042801", "transaction_type": "D/C", "payee": "D/C FROM KAINGA ORA", "memo": "3HLRPR 864878", "amount": "1903.66"
        }
        """,
        "result": """
        {
            "Unique Id": "2023042801", "transaction_type": "rental income"
        }
        """
    }, {
        "transaction": """
        {
            "Date": "31/03/2024", "Details": "Loan Payment", "Amount": "1496.83", "PrincipalBalance": "555217.82"
        }
        """,
        "result": """
        {
            "Unique Id": "31032024", "transaction_type": "capital deposit"
        }
        """
    }
]

header_filter_prefix = """
Given the following comma separated value content which may contain some metadata content followed by a list of
transactions, find the line where the transactions begin.
This will be header line of the transaction list
"""

header_filter_example_template = """
Here is an example:
<example>
Content:
{content}
result:
{result}
"""

header_filter_examples = [
    {
        "content": """
            Created date / time : 27 July 2024 / 17:21:57
            Bank 12; Branch 3273; Account 0018314-00 (Streamline)
            From date 20230401
            To date 20240331
            Ledger Balance : 5694.05 as of 20240727
            Date,Unique Id,Tran Type,Cheque Number,Payee,Memo,Amount
            
            2023/04/01,2023040101,LOAN INT,,"LOAN - INTEREST","12-3273-0018314-92 001 INTEREST",-796.92
            2023/04/28,2023042801,D/C,,"D/C FROM KAINGA ORA","3HLRPR 864878",1903.66
            2023/05/01,2023050101,LOAN INT,,"LOAN - INTEREST","12-3273-0018314-92 001 INTEREST",-771.22
            2023/05/07,2023050701,DEBIT,,"DEBIT","FC12-3148-0191417-00 dharsh",-450.00
            2023/05/31,2023053101,D/C,,"D/C FROM KAINGA ORA","3HLRPR 875665",1990.37
            2023/06/01,2023060101,LOAN INT,,"LOAN - INTEREST","12-3273-0018314-92 001 INTEREST",-796.92
            2023/06/13,2023061301,TFR OUT,,"MB TRANSFER","TO 12-3637- 0481933-00",-3000.00
            2023/06/30,2023063001,D/C,,"D/C FROM KAINGA ORA","3HLRPR 885644",1999.66
            2023/07/01,2023070101,LOAN INT,,"LOAN - INTEREST","12-3273-0018314-92 001 INTEREST",-771.22
            """,
        "result": """{
            "headers": "Date,Unique Id,Tran Type,Cheque Number,Payee,Memo,Amount"
            "line_number": 5
        }"""
    }
]

expenses_insights_prefix = """
As a book keeper for a residential rental company, Given a monthly breakdown of expenses. Find anomalies such as missing payments or payments recorded
with incorrect values. Typically a residential rental property would have expenses for mortgage interest, water, rates, insurance, 
at times some maintenance costs, sometimes management fees
"""

expenses_insights_example_template = """
Here is an example:
<example>
expenses:
{monthly_breakdown}
result:
{result}
"""

expenses_insights_examples = [
    {
        "monthly_breakdown": """[
            {
                "period": "April 2023",
                "expenses": {
                    "water": 94.50,
                    "rates": 657.45,
                    "management fee": 347,
                    "mortgage interest": 2450
                }
            },
            {
                "period": "May 2023",
                "expenses": {
                    "water": 89.35,
                    "management fee": 347,
                    "mortgage interest": 2550
                }
            },
            {
                "period": "June 2023",
                "expenses": {
                    "water": 99.50,
                    "management fee": 347,
                    "mortgage interest": 2450
                }
            },
            {
                "period": "July 2023",
                "expenses": {
                    "water": 104.06,
                    "rates": 657.45,
                    "management fee": 347,
                    "mortgage interest": 2550
                }
            },
            {
                "period":  "August 2023",
                "expenses": {
                    "water": 97.80,
                    "management fee": 347,
                    "mortgage interest": 2550
                }
            },
            {
                "period": "September 2023",
                "expenses": {
                    "water": 96.50,
                    "management fee": 347,
                    "mortgage interest": 4900
                }
            },
            {
                "period": "October 2023",
                "expenses": {
                    "water": 98.80,
                    "rates": 657.45,
                    "management fee": 347,
                    "mortgage interest": 2550
                }
            },
            {
                "period": "November 2023",
                "expenses": {
                    "management fee": 347,
                    "mortgage interest": 2450
                }
            },
            {
                "period": "December 2023",
                "expenses": {
                    "water": 81.45,
                    "management fee": 347,
                    "mortgage interest": 2550
                }
            },
            {
                "period": "January 2024",
                "expenses": {
                    "water": 76.45,
                    "rates": 657.45,
                    "management fee": 347,
                    "mortgage interest": 2550
                }
            },
            {
                "period": "February 2024",
                "expenses": {
                    "water": 85.67,
                    "management fee": 347,
                    "mortgage interest": 2400
                }
            },
            {
                "period": "March 2024",
                "expenses": {
                    "water": 93.50,
                    "management fee": 347,
                    "mortgage interest": 2550,
                    "insurance": 2580
                }
            },
        ]"""
        ,
        "result": """{
            "issues": [
                {"November 2023": "This month is missing the water expense which is usually a monthly expense, perhaps its been missed?"},
                {"September 2023": "This month has about twice the mortgage expense as other months, may be ins been incorrectly recorded? "},
            ]
        }"""
    }

]