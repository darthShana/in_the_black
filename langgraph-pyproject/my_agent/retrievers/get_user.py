from my_agent.model.user import UserInfo, Property, PropertyTypeEnum


class UserRetriever:

    @staticmethod
    def get_user(access_token: str) -> UserInfo:
        return UserInfo(
            # user_id='b5c7f883-eb98-4ef0-a744-1496510552c2'
            user_id='d3b0c891-41c6-49ba-95ee-4c33bf17cd3f',
            properties=[
                Property(
                    property_id="86fe1497-7595-428e-8b0e-feab35c278db",
                    address1='22 Fort Lincoln Loop,',
                    suburb='Karaka',
                    city='Papakura',
                    property_type=PropertyTypeEnum.House,
                    bedrooms=3,
                    assets=[]
                )
            ]

        )
