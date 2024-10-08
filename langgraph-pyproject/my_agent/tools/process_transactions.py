import logging
from typing import List

import boto3
from langchain_core.tools import StructuredTool

from my_agent.retrievers.file_loader import AWSCSVFileLoader, AWSPDFFileLoader
from my_agent.retrievers.get_user import UserRetriever
from my_agent.retrievers.transaction_retriever import TransactionRetriever

statement_retriever = TransactionRetriever()

s3 = boto3.client('s3')
log = logging.getLogger(__name__)


def load_transactions(file_name: str) -> dict[str, List[dict]]:
    log.info(f"loading bank transactions: {file_name}")
    user = UserRetriever.get_user("in here test")

    if file_name.endswith(".csv"):
        file_loader = AWSCSVFileLoader(
            client=s3,
            bucket="black-transactions-8e8f04a",
            key=f"{user.user_id}/{file_name}")
    else:
        file_loader = AWSPDFFileLoader(
            client=s3,
            bucket="black-transactions-8e8f04a",
            key=f"{user.user_id}/{file_name}")

    content = file_loader.load_content()
    transactions = statement_retriever.extract_transactions(content)
    return {'transactions': transactions}


load_transactions_tool_name = "load_transactions"
load_transactions_tool = StructuredTool.from_function(
    func=load_transactions,
    name=load_transactions_tool_name,
    description="""
        Useful to load transactions from an uploaded document so it can be processed
        """
)
