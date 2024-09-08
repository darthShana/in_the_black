from langsmith import unit

from my_agent.model.document import DocumentTypeEnum
from my_agent.model.user import UserInfo
from my_agent.tools.document_classifier import classify_document


@unit
def test_classify_document(monkeypatch):
    mock_user = UserInfo(
        user_id='d3b0c891-41c6-49ba-95ee-4c33bf17cd3f'
    )

    def mock_get_user(username):
        return mock_user

    assert classify_document('88752901-1001_Transactions_2023-04-01_2024-03-31.csv') == DocumentTypeEnum.BANK_STATEMENT
    assert classify_document('F Rental Statement.pdf') == DocumentTypeEnum.PROPERTY_MANAGER_STATEMENT
    assert classify_document('A Tower Insurance Confirmation.pdf') == DocumentTypeEnum.VENDOR_STATEMENT
