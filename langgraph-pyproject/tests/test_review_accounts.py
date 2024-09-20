import logging
from datetime import datetime

from langsmith import unit

from my_agent.model.user import UserInfo
from my_agent.retrievers.get_user import UserRetriever
from my_agent.tools.review_accounts import review_accounts

log = logging.getLogger(__name__)


@unit
def test_validate_transactions(monkeypatch):
    mock_user = UserInfo(
        user_id='d3b0c891-41c6-49ba-95ee-4c33bf17cd3f',
        properties=[]
    )

    def mock_get_user(username):
        return mock_user

    monkeypatch.setattr(UserRetriever, 'get_user', mock_get_user)

    issues = review_accounts(datetime(2023, 4, 1), datetime(2024, 3, 31))
    log.info(issues)
