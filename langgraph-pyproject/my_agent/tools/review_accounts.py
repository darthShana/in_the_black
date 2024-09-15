from datetime import datetime

from my_agent.tools.get_accounts import monthly_expenses


def review_accounts(start_date: datetime, end_date: datetime):
    expenses = monthly_expenses(start_date, end_date)
    