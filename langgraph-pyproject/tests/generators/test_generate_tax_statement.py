from datetime import datetime
from decimal import Decimal

from langsmith import unit

from my_agent.generators.tax_statement import generate_tax_statement
from my_agent.model.user import UserInfo
from my_agent.tools.get_accounts import get_accounts


@unit
def test_generate_tax_statement():
    user = UserInfo(
        user_id='d3b0c891-41c6-49ba-95ee-4c33bf17cd3f',
        properties=[]
    )

    start = datetime(2023, 4, 1)
    end = datetime(2024, 3, 31)
    accounts = get_accounts(start, end)
    tax_statement = generate_tax_statement(user.user_id, user.properties, end.year, accounts)

    assert tax_statement['income']['total_rents'] == Decimal('36535.71')
    assert tax_statement['income']['other_income_description'] == 'Water'
    assert tax_statement['income']['other_income'] == Decimal('112.49')
    assert tax_statement['income']['total_income'] == (Decimal('36535.71') + Decimal('112.49'))
