from datetime import datetime
from typing import List, Dict, Annotated

from langchain_core.tools import StructuredTool
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field

from my_agent.generators.statement_of_profit_or_loss import generate_statement_of_profit_or_loss
from my_agent.generators.tax_statement import generate_tax_statement
from my_agent.retrievers.get_user import UserRetriever
from my_agent.tools.get_accounts import get_accounts


class GenerateEnfOfYearReportInput(BaseModel):
    state: Annotated[dict, InjectedState]
    start: datetime = Field(description="get transactions after this date and time")
    end: datetime = Field(description="get transactions before this date and time")


def generate_end_of_year_reports(state: Annotated[dict, InjectedState], start: datetime, end: datetime) -> dict[str, dict]:
    user = UserRetriever.get_user("in here test")
    accounts = get_accounts(start, end)
    statement_of_profit_or_loss = generate_statement_of_profit_or_loss(accounts)
    tax_statement = generate_tax_statement(user.user_id, user.properties, end.year)
    return {
        "statement_of_profit_or_loss": statement_of_profit_or_loss,
        "tax": tax_statement
    }


generate_end_of_year_reports_tool_name = "generate_end_of_year_reports"
generate_end_of_year_reports_tool = StructuredTool.from_function(
    func=generate_end_of_year_reports,
    name=generate_end_of_year_reports_tool_name,
    description="""
        Useful to generate an end-of-year reports for a company
        """,
    args_schema=GenerateEnfOfYearReportInput,
)