import logging

from typing import List, Annotated
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import InjectedState
from pydantic.v1 import BaseModel, Field

from my_agent.retrievers.transaction_retriever import TransactionRetriever, available_transaction_types

log = logging.getLogger(__name__)
statement_retriever = TransactionRetriever()


class ClassifyTransactionsInput(BaseModel):
    confirm_filter: bool = Field(description="has the human confirmed that the filter be applied to transactions before classification")
    state: Annotated[dict, InjectedState] = Field(description="current state")


def classify_statement_transactions(confirm_filter: bool, state: Annotated[dict, InjectedState]) -> dict[str, List[dict]]:
    filtered = state['transactions']['transactions']
    log.info(f"classify_transactions-----:{len(filtered)} confirmed:{confirm_filter}")

    classifications = statement_retriever.classify_transactions(filtered)
    log.info(f"classified values from bank statement: {len(filtered)}")

    return {
        'transactions': [row | classified for (row, classified) in zip(filtered, classifications)],
        'available_transaction_types': available_transaction_types
    }


classify_bank_transactions_tool_name = "classify_bank_transactions"
classify_bank_transactions_tool = StructuredTool.from_function(
    func=classify_statement_transactions,
    name=classify_bank_transactions_tool_name,
    description="""
        Useful to classify transactions loaded from a document of type bank_statement
        """,
    args_schema=ClassifyTransactionsInput,
)

classify_property_management_transactions_tool_name = "classify_property_management_transactions"
classify_property_management_transactions_tool = StructuredTool.from_function(
    func=classify_statement_transactions,
    name=classify_property_management_transactions_tool_name,
    description="""
        Useful to classify transactions loaded from a document of type property_management_statement
        """,
    args_schema=ClassifyTransactionsInput,
)


