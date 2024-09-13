import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta

from my_agent.model.account import AccountTypeEnum
from my_agent.retrievers.get_user import UserRetriever
from my_agent.tools.get_accounts import get_accounts

log = logging.getLogger(__name__)


def company_overview(start_date: datetime, end_date: datetime) -> dict:
    current_date = start_date.replace(day=1)

    monthly_expenses = []
    while current_date <= end_date:
        last_day = (current_date + relativedelta(months=1, days=-1)).day
        log.info(f"Month: {current_date.strftime('%B %Y')}")
        accounts = get_accounts(current_date, current_date.replace(day=last_day))
        month = {
            'period': current_date.strftime('%B %Y'),
            'expenses': {account.display_name: account.balance() for account in accounts.values() if account.account_type == AccountTypeEnum.EXPENSES}
        }
        monthly_expenses.append(month)

        current_date += relativedelta(months=1)

    return {'monthly_expenses': monthly_expenses}
