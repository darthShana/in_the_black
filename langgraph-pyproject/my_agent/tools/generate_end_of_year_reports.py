from datetime import datetime
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field

from my_agent.generators.statement_of_profit_or_loss import generate_statement_of_profit_or_loss
from my_agent.generators.tax_statement import generate_tax_statement
from my_agent.retrievers.get_user import UserRetriever
from my_agent.retrievers.get_accounts import get_accounts


class GenerateEnfOfYearReportInput(BaseModel):
    config: RunnableConfig = Field(description="runnable config")
    start: datetime = Field(description="get transactions after this date and time")
    end: datetime = Field(description="get transactions before this date and time")


def generate_end_of_year_reports(config: RunnableConfig, start: datetime, end: datetime) -> dict[str, dict]:
    token = config.get("configurable", {}).get("access_token")
    user = UserRetriever.get_user(token)

    accounts = get_accounts(user, start, end)
    statement_of_profit_or_loss = generate_statement_of_profit_or_loss(accounts)
    tax_statement = generate_tax_statement(user.user_id, user.properties, end.year, accounts)
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