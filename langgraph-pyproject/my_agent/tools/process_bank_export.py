import json
import uuid
from typing import List, Annotated

import boto3
import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate, FewShotPromptWithTemplates
from langchain_core.tools import StructuredTool
from langchain_core.utils.json import parse_json_markdown
from langgraph.prebuilt import InjectedState
from pydantic.v1 import BaseModel, Field

from my_agent.model.transaction import BankAccountTypeEnum, Transaction
from my_agent.retrievers.bank_statement_retriever import BankStatementRetriever, available_transaction_types
from my_agent.retrievers.file_loader import AWSFileLoader
from my_agent.retrievers.get_user import UserRetriever
from my_agent.retrievers.header_filter import HeaderFilter

from my_agent.tools.templates import dto_mapping_example_template, dto_mapping_prefix, dto_mapping_examples

log = logging.getLogger(__name__)

s3 = boto3.client('s3')
dynamo = boto3.client('dynamodb')
chat = ChatAnthropic(model="claude-3-5-sonnet-20240620")
statement_retriever = BankStatementRetriever()

EXAMPLE_PROMPT2 = PromptTemplate(
    input_variables=["transaction", "result"], template=dto_mapping_example_template
)


def to_dynamo_items(customer_number: str, to_map: list[dict], bank_account_type: BankAccountTypeEnum) -> list[dict]:
    mandatory_values = [
        {
           "CustomID": "a unique transaction id"
        }, {
           "TransactionDate": "the date of this transaction"
        }, {
           "TransactionAmount": "the amount of this transaction"
        }
    ]

    prefix = PromptTemplate(
        input_variables=["mandatory_values"], template=dto_mapping_prefix
    )
    suffix = PromptTemplate(
        input_variables=["transactions"],
        template="""
            So given 
            transactions: 
            {{transactions}}. 
            Extract the result in json format marking the json as ```json:""",
    )

    prompt = FewShotPromptWithTemplates(
        suffix=suffix,
        prefix=prefix,
        input_variables=["mandatory_values", "transactions"],
        examples=BankStatementRetriever.escape_examples(dto_mapping_examples),
        example_prompt=EXAMPLE_PROMPT2,
        example_separator="\n",
    )

    chain = prompt | chat

    mapped = []
    batch_size = 20
    for i in range(0, len(to_map), batch_size):
        out = chain.invoke({"mandatory_values": mandatory_values, "transactions": to_map[i:i + batch_size]})
        mapped.extend(parse_json_markdown(out.content))

    log.info(f"mandatory values from bank statement: {len(mapped)}")

    ret = []
    for mand, orig in zip(mapped, to_map):
        ret.append({
            'TransactionID': {'S': str(uuid.uuid4())},
            'CustomerNumber': {'S': customer_number},
            'TransactionDate': {'S': mand['TransactionDate']},
            'TransactionType': {'S': orig['transaction_type']},
            'TransactionAmount': {'S': str(mand['TransactionAmount'])},
            'CustomID': {'S': str(mand['CustomID'])},
            'BankAccountType': {'S': json.dumps(bank_account_type)},
            'content': {
                'S': str(orig)
            }
        })

    return ret


def load_transactions(file_name: str) -> dict[str, List[dict]]:
    log.info(f"loading transactions: {file_name}")
    user = UserRetriever.get_user("in here test")

    file_loader = AWSFileLoader(
        client=s3,
        bucket="black-transactions-8e8f04a",
        key=f"{user.user_id}/{file_name}")

    header_filter = HeaderFilter(file_loader)
    df = header_filter.extract_transactions()
    return {'bank_transactions': df.to_dict("records")}


load_transactions_tool_name = "load_transactions"
load_transactions_tool = StructuredTool.from_function(
    func=load_transactions,
    name=load_transactions_tool_name,
    description="""
        Useful to load transactions from an uploaded file so it can be processed
        """
)


def filter_transactions(state: Annotated[dict, InjectedState]):
    log.info("filtering transactions")
    filtered = json.loads(state['transactions'])['bank_transactions']
    statement_filter = state['statement_filter']
    log.info(f"statement_filter: {statement_filter}")
    log.info(f"statement_filter type: {type(statement_filter)}")

    if statement_filter is not None:
        filtered = statement_retriever.filter_transactions(filtered, statement_filter)

    log.info(f"filtered records:{len(filtered)}")
    return {'bank_transactions': filtered}


filter_transactions_tool_name = "filter_transactions"
filter_transactions_tool = StructuredTool.from_function(
    func=filter_transactions,
    name=filter_transactions_tool_name,
    description="""
        Useful to filter transactions in a bank statement if the user wants to include or exclude some of them
        """,
)


class ClassifyTransactionsInput(BaseModel):
    state: Annotated[dict, InjectedState] = Field(description="current state")


def classify_transactions(state: Annotated[dict, InjectedState]) -> dict[str, List[dict]]:
    log.info('classify_transactions-----')
    filtered = json.loads(state['transactions'])['bank_transactions']

    classifications = statement_retriever.classify_transactions(filtered)
    log.info(f"classified values from bank statement: {len(filtered)}")

    return {
        'bank_transactions': [row | classified for (row, classified) in zip(filtered, classifications)],
        'available_transaction_types': available_transaction_types
    }


classify_transactions_tool_name = "classify_transactions"
classify_transactions_tool = StructuredTool.from_function(
    func=classify_transactions,
    name=classify_transactions_tool_name,
    description="""
        Useful to classify transactions in a bank statement
        """,
    args_schema=ClassifyTransactionsInput,
)


class SaveClassifiedTransactionsInput(BaseModel):
    state: Annotated[dict, InjectedState] = Field(description="current state")
    bank_account_type: BankAccountTypeEnum = Field(description="The kind of bank account this statement is for")


def save_classified_transactions(state: Annotated[dict, InjectedState], bank_account_type: BankAccountTypeEnum) -> bool:

    user = UserRetriever.get_user("in here test")
    transactions = json.loads(state['transactions'])['bank_transactions']
    mapped = to_dynamo_items(user.user_id, transactions, bank_account_type)

    for item in mapped:
        dynamo.put_item(TableName="Transactions", Item=item)
    return True


save_classified_transactions_tool_name = "save_transactions"
save_classified_transactions_tool = StructuredTool.from_function(
    func=save_classified_transactions,
    name=save_classified_transactions_tool_name,
    description="""
        Useful to save classified transactions in a bank statement
        """,
    args_schema=SaveClassifiedTransactionsInput,
)
