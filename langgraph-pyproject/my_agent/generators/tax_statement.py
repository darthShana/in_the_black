import decimal
import json
from datetime import datetime
from typing import List

import boto3
from boto3.dynamodb.conditions import Key, Attr

from my_agent.model.account import Account, AccountTypeEnum
from my_agent.model.user import Property, Asset, AssetTypeEnum
from my_agent.retrievers.ir_264 import calculate_depreciation

dynamodb = boto3.resource('dynamodb')


def to_asset(item: dict) -> Asset:
    asset_type_str = json.loads(item['AssetType'])
    asset_type_enum = AssetTypeEnum.from_string(asset_type_str)

    return Asset(
        asset_id=item['CustomerAssetsID'],
        property_id=item['PropertyID'],
        asset_type=asset_type_enum,
        installation_date=datetime.strptime(item['InstallationDate'], "%Y/%m/%d"),
        installation_value=decimal.Decimal(item['InstallationValue'])
    )


def get_other_revenue(accounts):
    filtered_accounts = []
    total_balance = 0

    for key, account in accounts.items():
        if (account.account_type == AccountTypeEnum.EXPENSES and account.balance() < 0) or \
                (account.account_type == AccountTypeEnum.REVENUE and account.balance() > 0 and 'rental_revenue' != key):
            filtered_accounts.append(account.display_name)
            total_balance += abs(account.balance())

    return ', '.join(filtered_accounts), total_balance


def generate_tax_statement(customer_id: str, properties: List[Property], year: int, accounts: dict[str, Account]):
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
            'asset': str(asset.asset_type),
            'date_purchase': asset.installation_date.strftime('%Y/%m/%d'),
            'cost': asset.installation_value,
            'opening_value': dep['opening_value'],
            'rate': dep['rate'],
            'method': 'DV',
            'depreciation': dep['depreciation'],
            'closing_value': dep['opening_value'] - dep['depreciation'],
        })

    (other_revenue_description, other_revenue) = get_other_revenue(accounts)

    income = {}
    if 'rental_revenue' in accounts:
        income['total_rents'] = accounts['rental_revenue'].balance()
    if other_revenue is not None:
        income['other_income'] = other_revenue
    if other_revenue_description is not None:
        income['other_income_description'] = other_revenue_description
    if 'rental_revenue' in accounts and other_revenue is not None:
        income['total_income'] = accounts['rental_revenue'].balance() + other_revenue

    return {
        'depreciation': depreciation,
        'income': income
    }
