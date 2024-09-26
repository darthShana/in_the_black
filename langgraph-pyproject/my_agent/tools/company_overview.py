import logging
from datetime import datetime
from math import ceil
from typing import Annotated

from langchain_core.tools import StructuredTool
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field

from my_agent.retrievers.get_user import UserRetriever
from my_agent.retrievers.property_valuation import get_market_data
from my_agent.tools.generate_end_of_year_reports import generate_end_of_year_reports
from my_agent.tools.get_accounts import monthly_expenses

log = logging.getLogger(__name__)


class CompanyOverviewInput(BaseModel):
    state: Annotated[dict, InjectedState] = Field(description="current state")
    start_date: datetime = Field(description="get company overview after this date and time")
    end_date: datetime = Field(description="get company overview before this date and time")


def company_overview(state: Annotated[dict, InjectedState], start_date: datetime, end_date: datetime) -> dict:
    current_date = start_date.replace(day=1)

    user = UserRetriever.get_user("in here test")

    monthly = monthly_expenses(current_date, end_date)

    all_accounts = generate_end_of_year_reports(state, start_date, end_date)
    market_info = get_market_data(user.properties[0])
    log.info(market_info)

    # Calculate the number of weeks
    diff = end_date - start_date
    weeks = ceil(diff.days / 7)

    annual_rental_revenue = next(item['balance'] for item in all_accounts['statement_of_profit_or_loss']['revenue_items'] if item['display_name'] == 'Rental Revenue') * 52 / weeks
    log.info(annual_rental_revenue)

    property_dict = user.properties[0].model_dump()
    property_dict['property_type'] = property_dict['property_type'].value

    return {
        'property_details': property_dict,
        'monthly_expenses': monthly,
        'p&l': all_accounts['statement_of_profit_or_loss']['gross_profit'] - all_accounts['statement_of_profit_or_loss']['expenses_total'],
        'yield': annual_rental_revenue / market_info.estimated_value,
        'market_yield': market_info.market_rental * 52 / market_info.estimated_value,
        'expenses': all_accounts['statement_of_profit_or_loss']['expenses_items'],
    }


company_overview_tool_name = "company_overview"
company_overview_tool = StructuredTool.from_function(
    func=company_overview,
    name=company_overview_tool_name,
    description="""
        Useful to get an overview of the companies performance
        """,
    args_schema=CompanyOverviewInput,
)
