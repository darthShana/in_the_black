transaction_classification_prefix = """
Given the following list of transactions for a residential property investment company. Classify each transaction
to one of the available transaction types bellow for book keeping purposes.

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
                "date": "2023/04/01",
                "id": "2023040101",
                "transaction_type": "LOAN INT",
                "payee": "LOAN - INTEREST",
                "memo": "12-3273-0018314-92 001 INTEREST",
                "amount": "-796.92"
            }
        """,
        "result": """
            {
                "Unique Id": "2023040101",
                "transaction_type": "loan_interest"
            }
        """
    },
    {
        "transaction": """
        {
            "date": "2023/04/28",
            "id": "2023042801",
            "transaction_type": "D/C",
            "payee": "D/C FROM KAINGA ORA",
            "memo": "3HLRPR 864878",
            "amount": "1903.66"
        }
        """,
        "result": """
        {
            "Unique Id": "2023042801",
            "transaction_type": "rental_income"
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

transaction_filter_prefix = """
Given the following json filter, Generate am equivalent python regular expression that can filter transactions in a bank statement. 
The regex should match the field names as well as the values specified.  
"""

transaction_filter_example_template = """
Here is an example:
<example>
Filter:
{filter}
Result:
{result}
"""


transaction_filter_examples = [
    {
        "filter": """{
            '$or': [
                {
                    '$and': [
                        {'Payee': {'$eq': 'AUCKLAND COUNCIL'}},
                        {'Memo': {'$contain': '34 Nicholas'}}
                    ]
                }, {'Memo': {'$eq': 'D/D 5398975-01 WATERCARE'}
                }, {'Payee': {'$eq': 'ASB BANK Insurance'}
                }
            ]
        }
        """,
        "result": """{
            'regex': '(?:(?=.*(?:Payee:.*AUCKLAND COUNCIL|Memo:.*34 Nicholas).*(?:Payee:.*AUCKLAND COUNCIL|Memo:.*34 Nicholas))|(?=.*Memo:.*D/D 5398975-01 WATERCARE)|(?=.*Payee:.*ASB BANK Insurance))'
        }"""
    }
]
