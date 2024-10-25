from datetime import date
from decimal import Decimal
from enum import Enum
from typing import List

from pydantic import Field, BaseModel


class PropertyTypeEnum(str, Enum):
    House = "House"
    Flat = "Flat"


class AssetTypeEnum(Enum):
    DEFAULT = "Chattels(default class)"
    AIR_CONDITIONERS = "Air conditioners and heat pumps (through wall or window type)"
    AIR_VENTILATION = "Air ventilation systems( in roof cavity)"
    ALARMS = "Alarms(burglar / smoke, wired or wireless)"
    APPLIANCES_SMALL = "Appliances(small)"
    AWNINGS = "Awnings"
    BEDDING = "Bedding"
    BLINDS = "Blinds"
    CARPETS = "Carpets"
    CLOTHESLINES = "Clotheslines"
    CROCKERY = "Crockery"
    CURTAINS = "Curtains"
    CUTLERY = "Cutlery"
    DEHUMIDIFIERS = "Dehumidifiers(portable)"
    DISHWASHERS = "Dishwashers"
    DRAPES = "Drapes"
    DRYERS = "Dryers(clothes, domestic type)"
    FREEZERS = "Freezers(domestic type)"
    FURNITURE = "Furniture(loose)"
    GLASSWARE = "Glassware"
    HEATERS_ELECTRIC = "Heaters(electric)"
    HEATERS_OTHER = "Heaters(gas, portable and not flued)"
    LAWNMOWERS = "Lawn mowers"
    LIGHT_SHADES = "Light shades / fashion items affixed to a standard light fitting*"
    LINEN = "Linen"
    MAILBOXES = "Mailboxes"
    MICROWAVE_OVENS = "Microwave ovens"
    OVENS = "Ovens"
    REFRIGERATORS = "Refrigerators(domestic type)"
    SATELLITE_DISHES = "Satellite receiving dishes"
    STEREOS = "Stereos"
    STOVES = "Stoves"
    TELEVISIONS = "Televisions"
    UTENSILS = "Utensils(including pots and pans)"
    VACUUM_CLEANERS = "Vacuum cleaners(domestic type)"
    WASHING_MACHINES = "Washing machines(domestic type)"
    WASTE_DISPOSAL_UNITS = "Waste disposal units(domestic type)"
    WATER_HEATERS_HEAT_PUMP = "Water heaters(heat pump type)"
    WATER_HEATERS_OVER_SINK = "Water heaters(over - sink type)"
    WATER_HEATERS_OTHER = "Water heaters(other eg, electric or gas hot water cylinders)"
    WATER_HEATERS_SOLAR = "Water heaters(solar type)"

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, string_value):
        try:
            return cls[string_value]
        except KeyError:
            raise ValueError(f"'{string_value}' is not a valid {cls.__name__}")


class Asset(BaseModel):
    asset_id: str = Field(description="a unique id for this asset")
    asset_type: AssetTypeEnum = Field(description="type of asset")
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
    email: str= Field(description="user email address")
    first_name: str= Field(description="user first name")
    last_name: str= Field(description="user last name")
    properties: List[Property] = Field(description="list of properties for this user")
