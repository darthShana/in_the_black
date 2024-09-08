import logging
from typing import List, Annotated

import boto3
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import InjectedState
from pydantic.v1 import BaseModel, Field

from my_agent.retrievers.file_loader import AWSPDFFileLoader
from my_agent.retrievers.get_user import UserRetriever
from my_agent.retrievers.transaction_retriever import TransactionRetriever

log = logging.getLogger(__name__)
s3 = boto3.client('s3')
transaction_retriever = TransactionRetriever()


class ClassifyTransactionsInput(BaseModel):
    file_name: str = Field(description="file name of the statement with transactions to be classified")
    state: Annotated[dict, InjectedState] = Field(description="current state")


def classify_vendor_transactions(file_name: str, state: Annotated[dict, InjectedState]) -> dict[str, List[dict]]:
    log.info(f"loading vendor transactions: {file_name}")
    user = UserRetriever.get_user("in here test")

    file_loader = AWSPDFFileLoader(
        client=s3,
        bucket="black-transactions-8e8f04a",
        key=f"{user.user_id}/{file_name}")

    images_bytes = file_loader.load_content()
    service = transaction_retriever.classify_image(images_bytes[0])
    transactions = state['transactions']['transactions']
    for transaction in transactions:
        transaction['transaction_type'] = service['selected_service']

    return {
        'transactions': transactions
    }


classify_vendor_transactions_tool_name = "classify_vendor_transactions"
classify_vendor_transactions_tool = StructuredTool.from_function(
    func=classify_vendor_transactions,
    name=classify_vendor_transactions_tool_name,
    description="""
        Useful to classify transactions from an uploaded document of type vendor_statement so it can be saved
        """,
    args_schema=ClassifyTransactionsInput,
)
