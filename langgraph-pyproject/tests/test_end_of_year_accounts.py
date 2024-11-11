import logging
from datetime import datetime
from decimal import Decimal
from langsmith import unit

from my_agent.tools.generate_end_of_year_reports import generate_end_of_year_reports, generate_end_of_year_reports_internal
from tests.test_get_accounts import to_transaction

log = logging.getLogger(__name__)


@unit
def test_generate_profit_or_loss_dharsh(sample_transaction_types, sample_transaction_file, sample_transaction_file2, monkeypatch):
    transactions = [to_transaction(row, transaction_type) for row, transaction_type in zip(
        sample_transaction_file.to_dict('records'),
        sample_transaction_types.to_dict('records'))]
    transactions.extend([to_transaction(row, {'transaction_type': row['transaction_type']}) for row in sample_transaction_file2.to_dict('records')])
    transactions = [transaction for transaction in transactions if datetime(2023, 4, 1) <= transaction.date <= datetime(2024, 3, 31)]

    def mock_get_transactions(user_id, start, end):
        return transactions

    monkeypatch.setattr("my_agent.tools.get_accounts.get_transactions", mock_get_transactions)
    reports = generate_end_of_year_reports_internal(datetime(2023, 4, 1), datetime(2024, 3, 31))

    pl = reports['statement_of_profit_or_loss']

    assert next(obj for obj in pl['revenue_items'] if obj['display_name'] == 'Rental Revenue')['balance'] == Decimal('35458.69')
    assert pl['gross_profit'] == Decimal('35458.69')

    assert next(obj for obj in pl['expenses_items'] if obj['display_name'] == 'Mortgage Interest')['balance'] == Decimal('20639.56')
    assert next(obj for obj in pl['expenses_items'] if obj['display_name'] == 'Water')['balance'] == Decimal('3188.26')
    assert next(obj for obj in pl['expenses_items'] if obj['display_name'] == 'Rates')['balance'] == Decimal('2629.31')
    assert next(obj for obj in pl['expenses_items'] if obj['display_name'] == 'Insurance')['balance'] == Decimal('2260.92')
    assert pl['expenses_total'] == Decimal('28718.05')
