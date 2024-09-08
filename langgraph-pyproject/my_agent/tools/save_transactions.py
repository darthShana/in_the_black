import json
import logging
import uuid
from typing import Annotated

import boto3
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate, FewShotPromptWithTemplates
from langchain_core.tools import StructuredTool
from langchain_core.utils.json import parse_json_markdown
from langgraph.prebuilt import InjectedState
from pydantic.v1 import BaseModel, Field

from my_agent.model.transaction import BankAccountTypeEnum
from my_agent.retrievers.get_user import UserRetriever
from my_agent.retrievers.utils import escape_examples
from my_agent.tools.templates import dto_mapping_example_template, dto_mapping_prefix, dto_mapping_examples

log = logging.getLogger(__name__)

chat = ChatAnthropic(model="claude-3-5-sonnet-20240620")
dynamo = boto3.client('dynamodb')

EXAMPLE_PROMPT2 = PromptTemplate(
    input_variables=["transaction", "result"], template=dto_mapping_example_template
)


def to_dynamo_items(customer_number: str, to_map: list[dict], bank_account_type: BankAccountTypeEnum) -> list[dict]:
    mandatory_values = [
        {
           "CustomID": "a unique transaction id"
        }, {
           "TransactionDate": "the date of this transaction in format 'YYYY/MM/DD"
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
            Extract the result in json format list marking the json as ```json:""",
    )

    prompt = FewShotPromptWithTemplates(
        suffix=suffix,
        prefix=prefix,
        input_variables=["mandatory_values", "transactions"],
        examples=escape_examples(dto_mapping_examples),
        example_prompt=EXAMPLE_PROMPT2,
        example_separator="\n",
    )

    chain = prompt | chat

    mapped = []
    batch_size = 20
    for i in range(0, len(to_map), batch_size):
        out = chain.invoke({"mandatory_values": mandatory_values, "transactions": to_map[i:i + batch_size]})
        markdown = parse_json_markdown(out.content)
        mapped.extend(markdown)

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


class SaveClassifiedTransactionsInput(BaseModel):
    state: Annotated[dict, InjectedState] = Field(description="current state")
    bank_account_type: BankAccountTypeEnum = Field(description="The kind of bank account this statement is for")
    confirm_save: bool = Field(description="has the human confirmed saving these transactions")


def save_classified_transactions(state: Annotated[dict, InjectedState], bank_account_type: BankAccountTypeEnum, confirm_save: bool) -> bool:
    log.info(f"confirm_save is {confirm_save}")
    user = UserRetriever.get_user("in here test")
    transactions = state['transactions']['transactions']
    mapped = to_dynamo_items(user.user_id, transactions, bank_account_type)

    for item in mapped:
        dynamo.put_item(TableName="Transactions", Item=item)
    return True


save_classified_transactions_tool_name = "save_transactions"
save_classified_transactions_tool = StructuredTool.from_function(
    func=save_classified_transactions,
    name=save_classified_transactions_tool_name,
    description="""
        Useful to save classified transactions
        """,
    args_schema=SaveClassifiedTransactionsInput,
)