from langsmith import unit

from my_agent.model.user import UserInfo
from my_agent.retrievers.get_user import UserRetriever
from my_agent.tools.process_transactions import load_transactions


@unit
def test_load_vendor_transactions(monkeypatch):
    mock_user = UserInfo(
        user_id='d3b0c891-41c6-49ba-95ee-4c33bf17cd3f'
    )

    def mock_get_user(username):
        return mock_user

    monkeypatch.setattr(UserRetriever, 'get_user', mock_get_user)

    transactions = load_transactions("A Tower Insurance Confirmation.pdf")
    assert len(transactions['transactions']) == 12


@unit
def test_load_management_statement(property_management_transactions):
    assert len(property_management_transactions['transactions']) == 35
    for transaction in property_management_transactions['transactions']:
        assert 'date' in transaction
        assert 'moneyOut' in transaction
        assert 'moneyIn' in transaction

