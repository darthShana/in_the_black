import logging
from datetime import datetime
from decimal import Decimal

from my_agent.tools.company_overview import company_overview
log = logging.getLogger(__name__)


def test_company_overview():
    overview = company_overview(datetime(2023, 4, 1), datetime(2024, 3, 31))
    log.info(overview)

    monthly_expense_ = overview['monthly_expenses']
    assert len(monthly_expense_) == 12
    assert monthly_expense_[0]['period'] == 'April 2023'
    assert monthly_expense_[0]['expenses']['Water'] == Decimal('-80')
    assert monthly_expense_[0]['expenses']['Management Fees'] == Decimal('164.32')
    assert monthly_expense_[0]['expenses']['Insurance'] == Decimal('165.61')
    assert monthly_expense_[0]['expenses']['Mortgage Interest'] == Decimal('2594.99')
