import logging

import pytest
from langsmith import unit

from my_agent.model.user import UserInfo
from my_agent.retrievers.get_user import UserRetriever
from my_agent.tools.process_vendor_statement import classify_vendor_transactions

log = logging.getLogger(__name__)


@unit
@pytest.mark.no_cache
def test_classify_vendor_transactions(monkeypatch):
    mock_user = UserInfo(
        user_id='d3b0c891-41c6-49ba-95ee-4c33bf17cd3f',
        properties=[]
    )

    def mock_get_user(username):
        return mock_user

    monkeypatch.setattr(UserRetriever, 'get_user', mock_get_user)
    state = {'transactions': {}}
    state['transactions']['transactions'] = [{'date': '31 December 2023', 'amount': 165.61, 'detail': 'Payment'}, {'date': '31 January 2024', 'amount': 162.48, 'detail': 'Payment'}]

    transactions = classify_vendor_transactions("A Tower Insurance Confirmation.pdf", False, state)
    assert len(transactions['transactions']) == 2
    for transaction in transactions['transactions']:
        assert transaction['transaction_type'] == 'insurance'
