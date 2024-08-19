from my_agent.model.user import UserInfo


class UserRetriever:

    @staticmethod
    def get_user(access_token: str) -> UserInfo:
        return UserInfo(
            user_id='b5c7f883-eb98-4ef0-a744-1496510552c2'
        )
