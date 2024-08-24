from typing import List, Dict

from langchain_core.tools import StructuredTool
from pydantic.v1 import BaseModel, Field

from my_agent.generators.statement_of_profit_or_loss import generate_statement_of_profit_or_loss
from my_agent.model.account import Account


class GenerateEnfOfYearReportInput(BaseModel):
    accounts: Dict[str, Account] = Field(description="")


def generate_end_of_year_reports(accounts: Dict[str, Account]) -> Dict[str, str]:
    statement_of_profit_or_loss = generate_statement_of_profit_or_loss(accounts)
    return {
        "statement_of_profit_or_loss": statement_of_profit_or_loss
    }


generate_end_of_year_reports_tool_name = "get_accounts"
generate_end_of_year_reports_tool = StructuredTool.from_function(
    func=generate_end_of_year_reports,
    name=generate_end_of_year_reports_tool_name,
    description="""
        Useful to generate an end-of-year reports for a company
        """,
    args_schema=GenerateEnfOfYearReportInput,
)