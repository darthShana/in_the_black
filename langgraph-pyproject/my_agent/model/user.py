from pydantic.v1 import Field, BaseModel


class UserInfo(BaseModel):
    user_id: str = Field(description="user identifier")
