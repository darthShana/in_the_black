import json
import logging
import uuid
from typing import Annotated

import boto3
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate, FewShotPromptWithTemplates
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from langchain_core.utils.json import parse_json_markdown
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field

from my_agent.model.transaction import BankAccountTypeEnum
from my_agent.retrievers.get_user import UserRetriever
from my_agent.retrievers.utils import escape_examples
from my_agent.tools.templates import dto_mapping_example_template, dto_mapping_prefix, dto_mapping_examples

log = logging.getLogger(__name__)

chat = ChatAnthropic(model="claude-3-5-sonnet-20240620", max_tokens=4096)
dynamo = boto3.client('dynamodb')

EXAMPLE_PROMPT2 = PromptTemplate(
    input_variables=["transaction", "result"], template=dto_mapping_example_template
)


def to_dynamo_items(customer_number: str, to_map: list[dict], bank_account_type: BankAccountTypeEnum) -> list[dict]:
    mandatory_values = [
        {
           "UniqueID": "a unique transaction id, if none present, generate one using the date and other details"
        }, {
           "TransactionDate": "the date of this transaction in format 'YYYY/MM/DD"
        }, {
           "TransactionAmount": "the amount of this transaction, extracted as a positive amount"
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
    batch_size = 40
    for i in range(0, len(to_map), batch_size):
        out = chain.invoke({"mandatory_values": mandatory_values, "transactions": to_map[i:i + batch_size]})
        markdown = parse_json_markdown(out.content)
        if isinstance(markdown, list):
            mapped.extend(markdown)
        else:
            mapped.append(markdown)

    log.info(f"mandatory values from bank statement: {len(mapped)}")
    log.info(mapped[0])

    ret = []
    for mand, orig in zip(mapped, to_map):
        ret.append({
            'TransactionID': {'S': str(uuid.uuid4())},
            'CustomerNumber': {'S': customer_number},
            'TransactionDate': {'S': mand['TransactionDate']},
            'TransactionType': {'S': orig['transaction_type']},
            'TransactionAmount': {'S': str(mand['TransactionAmount'])},
            'CustomID': {'S': str(mand['UniqueID'])},
            'BankAccountType': {'S': json.dumps(bank_account_type)},
            'content': {
                'S': str(orig)
            }
        })

    return ret


class SaveClassifiedTransactionsInput(BaseModel):
    config: RunnableConfig = Field(description="runnable config")
    state: Annotated[dict, InjectedState] = Field(description="current state")
    account_type: BankAccountTypeEnum = Field(description="The kind of account this statement is for")
    confirm_save: bool = Field(description="has the human confirmed saving these transactions")


def save_classified_transactions(config: RunnableConfig, state: Annotated[dict, InjectedState], account_type: BankAccountTypeEnum, confirm_save: bool) -> bool:
    log.info(f"confirm_save is {confirm_save}")
    token = config.get("configurable", {}).get("access_token")
    user = UserRetriever.get_user(token)

    transactions = state['transactions']['transactions']
    mapped = to_dynamo_items(user.user_id, transactions, account_type)

    log.info(f"saving records to dynamo:{len(mapped)}")
    for item in mapped:
        try:
            dynamo.put_item(TableName="Transactions", Item=item)
        except Exception as e:
            log.error(e)

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
