from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List

from pydantic import Field, BaseModel


class PropertyTypeEnum(str, Enum):
    House = "House"
    Flat = "Flat"


class Asset(BaseModel):
    asset_id: str = Field(description="a unique id for this asset")
    asset_type: str = Field(description="type of asset")
    installation_date: date = Field(description="date of installation")
    installation_value: Decimal = Field(description="value of the asset at the time of installation")


class Property(BaseModel):
    property_id: str = Field(description="unique property id")
    address1: str = Field(description="first line of the property address")
    suburb: str = Field(description="suburb of the property")
    city: str = Field(description="city of the property")
    property_type: PropertyTypeEnum = Field(description="type of property")
    bedrooms: int = Field(description="number of bedrooms in the property")


class Valuation(BaseModel):
    estimated_value: Decimal = Field(description="estimated value for the property")
    market_rental: Decimal = Field(description="market rental value for the property")


class UserInfo(BaseModel):
    user_id: str = Field(description="user identifier")
    properties: List[Property] = Field(description="list of properties for this user")
