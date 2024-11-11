import logging
from datetime import datetime
from decimal import Decimal
from math import ceil

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from my_agent.retrievers.get_user import UserRetriever
from my_agent.retrievers.metadata import get_metadata
from my_agent.retrievers.property_valuation import get_market_data
from my_agent.tools.generate_end_of_year_reports import generate_end_of_year_reports_internal
from my_agent.retrievers.get_accounts import monthly_expenses

log = logging.getLogger(__name__)


class CompanyOverviewInput(BaseModel):
    config: RunnableConfig = Field(description="runnable config")
    start_date: datetime = Field(description="get company overview after this date and time")
    end_date: datetime = Field(description="get company overview before this date and time")


def company_overview(config: RunnableConfig, start_date: datetime, end_date: datetime) -> dict:
    token = config.get("configurable", {}).get("access_token")
    user = UserRetriever.get_user(token)

    current_date = start_date.replace(day=1)

    metadata = get_metadata()

    monthly = monthly_expenses(user, current_date, end_date)

    end_of_year = generate_end_of_year_reports_internal(config, start_date, end_date)
    market_info = get_market_data(user.properties[0])
    log.info("market_info")
    log.info(market_info)

    # Calculate the number of weeks
    diff = end_date - start_date
    weeks = ceil(diff.days / 7)

    annual_rental_revenue = next(
        (item['balance'] for item in end_of_year['statement_of_profit_or_loss']['revenue_items'] if item['display_name'] == 'Rental Revenue'),
        Decimal(0)
    ) * 52 / weeks
    log.info(f"annual_rental_revenue: {annual_rental_revenue}")

    property_assets = [asset for asset in end_of_year['tax']['depreciation']]

    property_dict = user.properties[0].model_dump()
    property_dict['property_type'] = property_dict['property_type'].value

    return {
        'metadata': metadata,
        'property_details': property_dict,
        'property_assets': property_assets,
        'monthly_expenses': monthly,
        'p&l': float(end_of_year['statement_of_profit_or_loss']['gross_profit'] - end_of_year['statement_of_profit_or_loss']['expenses_total']),
        'yield': annual_rental_revenue / float(market_info.estimated_value),
        'market_yield': float(market_info.market_rental * 52 / market_info.estimated_value),
        'expenses': [{'display_name': item['display_name'], 'balance': float(item['balance'])} for item in end_of_year['statement_of_profit_or_loss']['expenses_items']],
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
