import decimal
from datetime import datetime
from typing import List

import boto3
from boto3.dynamodb.conditions import Key, Attr

from my_agent.model.user import Property, Asset
from my_agent.retrievers.ir_264 import calculate_depreciation

dynamodb = boto3.resource('dynamodb')


def to_asset(dynamo_record: dict) -> Asset:
    return Asset(
        asset_id=dynamo_record['CustomerAssetsID'],
        property_id=dynamo_record['PropertyID'],
        asset_type=dynamo_record['AssetType'],
        installation_date=datetime.strptime(dynamo_record['InstallationDate'], '%Y/%m/%d'),
        installation_value=decimal.Decimal(dynamo_record['TransactionAmount'])
    )


def generate_tax_statement(customer_id: str, properties: List[Property], year: int):
    table = dynamodb.Table('CustomerAssets')

    property_attr = boto3.dynamodb.conditions.Attr('PropertyID')
    customer_attr = boto3.dynamodb.conditions.Attr('CustomerNumber')
    response = table.scan(
        FilterExpression=
        customer_attr.eq(customer_id)
    )

    assets = [to_asset(i) for i in response['Items']]
    depreciation = []
    for asset in assets:
        dep = calculate_depreciation(asset, year)
        depreciation.append({
            'asset': asset.asset_type,
            'date_purchase': asset.installation_date,
            'cost': asset.installation_value,
            'opening_value': dep['opening_value'],
            'rate': dep['rate'],
            'method': 'DV',
            'depreciation': dep['depreciation'],
            'closing_value': dep['opening_value'] - dep['depreciation'],
        })

    return {
        'depreciation': depreciation
    }
