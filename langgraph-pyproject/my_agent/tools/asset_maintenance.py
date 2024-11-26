import json
import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field

from my_agent.retrievers.get_user import UserRetriever
from my_agent.utils.aws_credentials import AWSSessionFactory


class AssetInput(BaseModel):
    config: RunnableConfig = Field(description="rannable config")
    asset_type: str = Field(description="type of asset")
    installation_date: date = Field(description="date of installation")
    installation_value: Decimal = Field(description="value of the asset at the time of installation")


def add_asset(config: RunnableConfig, asset_type: str, installation_date: date, installation_value: Decimal):
    aws = AWSSessionFactory()
    dynamo = aws.get_session().client('dynamodb')

    token = config.get("configurable", {}).get("access_token")
    user = UserRetriever.get_user(token)

    dynamo.put_item(TableName="CustomerAssets", Item={
            'CustomerAssetsID': {'S': str(uuid.uuid4())},
            'CustomerNumber': {'S': user.user_id},
            'PropertyID': {'S': user.properties[0].property_id},
            'AssetType': {'S': json.dumps(asset_type)},
            'InstallationDate': {'S': installation_date.strftime("%Y/%m/%d")},
            'InstallationValue': {'S': str(installation_value)},
        })


add_asset_tool_name = "add_asset"
add_asset_tool = StructuredTool.from_function(
    func=add_asset,
    name=add_asset_tool_name,
    description="""
        Useful to add assets to a property
        """,
    args_schema=AssetInput,
)
