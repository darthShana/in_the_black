import logging
from decimal import Decimal

from my_agent.retrievers.company_insights import review_expenses

log = logging.getLogger(__name__)

monthly_expenses = [
    {'period': 'April 2023', 'expenses': {'Management Fees': Decimal('164.32'), 'Water': Decimal('-80'), 'Mortgage Interest': Decimal('2594.99'), 'Insurance': Decimal('165.61')}},
    {'period': 'May 2023', 'expenses': {'Water': Decimal('45.35'), 'Management Fees': Decimal('205.4'), 'Mortgage Interest': Decimal('2507.55'), 'Insurance': Decimal('165.61')}},
    {'period': 'June 2023', 'expenses': {'Mortgage Interest': Decimal('2587.84'), 'Water': Decimal('-80'), 'Management Fees': Decimal('164.32'), 'Insurance': Decimal('165.61')}},
    {'period': 'July 2023', 'expenses': {'Water': Decimal('-6.63'), 'Management Fees': Decimal('164.32'), 'Insurance': Decimal('165.61')}},
    {'period': 'August 2023',
     'expenses': {'Maintenance Expenses': Decimal('149.5'), 'Management Fees': Decimal('619.94'), 'Mortgage Interest': Decimal('2581.08'), 'Rates': Decimal('552.83'),
                  'Insurance': Decimal('165.61')}},
    {'period': 'September 2023',
     'expenses': {'Water': Decimal('-28'), 'Mortgage Interest': Decimal('2577.64'), 'Management Fees': Decimal('31.64'), 'Insurance': Decimal('165.61')}},
    {'period': 'October 2023', 'expenses': {'Mortgage Interest': Decimal('2490.67'), 'Water': Decimal('30'), 'Management Fees': Decimal('88.59'), 'Insurance': Decimal('165.61')}},
    {'period': 'November 2023', 'expenses': {'Management Fees': Decimal('63.27'), 'Water': Decimal('189.6'), 'Rates': Decimal('552.83'), 'Mortgage Interest': Decimal('2570.56'),
                                             'Insurance': Decimal('165.61')}},
    {'period': 'December 2023', 'expenses': {'Mortgage Interest': Decimal('2484.36'), 'Management Fees': Decimal('63.27'), 'Water': Decimal('30'), 'Insurance': Decimal('165.61')}},
    {'period': 'January 2024', 'expenses': {'Water': Decimal('37'), 'Mortgage Interest': Decimal('2564.08'), 'Insurance': Decimal('162.48')}},
    {'period': 'February 2024',
     'expenses': {'Rates': Decimal('278.4'), 'Mortgage Interest': Decimal('2559.46'), 'Management Fees': Decimal('552.83'), 'Insurance': Decimal('162.63')}},
    {'period': 'March 2024', 'expenses': {'Water': Decimal('134.37'), 'Mortgage Interest': Decimal('2392.0'), 'Management Fees': Decimal('110.6'), 'Insurance': Decimal('162.63')}}
]


def test_company_insights():
    expense_insights = review_expenses(monthly_expenses, [])
    log.info(expense_insights)
    assert 1 >= expense_insights['issues']


def test_company_insights_with_exceptions():
    exceptions = [
        {
            "period": "April 2023",
            "reason": "My water bills can be negative as its refunded by the tenant sometimes"
        }
    ]
    expense_insights = review_expenses(monthly_expenses, exceptions)
    log.info(expense_insights)

