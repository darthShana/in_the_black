from decimal import Decimal
from enum import Enum
from typing import List

from pydantic.v1 import Field, BaseModel


class PropertyTypeEnum(str, Enum):
    House = "House"
    Flat = "Flat"


class Property(BaseModel):
    address1: str = Field(description="first line of the property address")
    suburb: str = Field(description="suburb of the property")
    city: str = Field(description="city of the property")
    property_type: PropertyTypeEnum = Field(description="type of property")
    bedrooms: str = Field(description="number of bedrooms in the property")


class Valuation(BaseModel):
    estimated_value: Decimal = Field(description="estimated value for the property")
    market_rental: Decimal = Field(description="market rental value for the property")


class UserInfo(BaseModel):
    user_id: str = Field(description="user identifier")
    properties: List[Property]
