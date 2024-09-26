import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

import boto3
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import InjectedState
from pydantic import BaseModel, Field

from my_agent.retrievers.get_user import UserRetriever

dynamo = boto3.client('dynamodb')


class AssetInput(BaseModel):
    state: Annotated[dict, InjectedState] = Field(description="current state")
    property_id: str = Field(description="property this asset is installed in")
    asset_type: str = Field(description="type of asset")
    installation_date: date = Field(description="date of installation")
    installation_value: Decimal = Field(description="value of the asset at the time of installation")


def add_asset(state: Annotated[dict, InjectedState], asset_type: str, installation_date: date, installation_value: Decimal):
    user = UserRetriever.get_user("in here test")

    dynamo.put_item({
            'CustomerAssetsID': {'S': str(uuid.uuid4())},
            'CustomerNumber': {'S': user.user_id},
            'PropertyID': {'S': user.properties[0]},
            'AssetType': {'S': asset_type},
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
