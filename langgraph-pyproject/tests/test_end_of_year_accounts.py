import logging
from datetime import datetime
from pprint import pprint

from langsmith import unit

from tests.test_get_accounts import to_overrides
from tests.test_process_bank_export import customer_number
from my_agent.tools.generate_end_of_year_reports import generate_end_of_year_reports
from my_agent.tools.get_accounts import get_accounts
from my_agent.retrievers.get_transactions import get_transactions
from bs4 import BeautifulSoup


log = logging.getLogger(__name__)


@unit
def test_generate_profit_or_loss(upload_transactions: bool, sample_transaction_overrides, chart_of_accounts):
    transactions = get_transactions(customer_number, datetime(2023, 4, 1), datetime(2024, 3, 31))
    check = [transaction for transaction in transactions if transaction.transaction_type == "water"]
    log.info(pprint(check, compact=True))

    transaction_overrides = to_overrides(transactions, sample_transaction_overrides.to_dict('records'))
    accounts = get_accounts(transactions, chart_of_accounts, transaction_overrides)

    reports = generate_end_of_year_reports(accounts)

    soup = BeautifulSoup(reports['statement_of_profit_or_loss'], features="html5lib")

    rental_revenue = [td.find_next_sibling('td').text for td in soup.find_all('td') if td.text == 'Rental Revenue'][0]
    gross_profit = [td.find_next_sibling('td').text for td in soup.find_all('td') if td.text == 'Gross Profit'][0]
    mortgage_interest = [td.find_next_sibling('td').text for td in soup.find_all('td') if td.text == 'Mortgage Interest'][0]
    water = [td.find_next_sibling('td').text for td in soup.find_all('td') if td.text == 'Water'][0]
    rates = [td.find_next_sibling('td').text for td in soup.find_all('td') if td.text == 'Rates'][0]
    insurance = [td.find_next_sibling('td').text for td in soup.find_all('td') if td.text == 'Insurance'][0]
    total_expenses = [td.find_next_sibling('td').text for td in soup.find_all('td') if td.text == 'Total Expenses'][0]

    assert rental_revenue == '35458.69'
    assert gross_profit == '35458.69'

    assert mortgage_interest == '20639.56'
    assert water == '3188.26'
    assert rates == '2629.31'
    assert insurance == '2260.92'
    assert total_expenses == '28718.05'
