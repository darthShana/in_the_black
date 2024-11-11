import logging
from typing import Dict

from my_agent.model.account import Account, AccountTypeEnum

log = logging.getLogger(__name__)


def generate_statement_of_financial_position(accounts: Dict[str, Account]) -> dict:

    asset_items = filter_accounts(accounts, AccountTypeEnum.ASSET)
    assets_total = sum(account['balance'] for account in asset_items)

    liability_items = filter_accounts(accounts, AccountTypeEnum.LIABILITY)
    liabilities_total = sum(account['balance'] for account in liability_items)

    equity_items = filter_accounts(accounts, AccountTypeEnum.EQUITY)
    equity_total = sum(account['balance'] for account in equity_items)

    return {
            'asset_items': asset_items,
            'asset_total': assets_total,
            'liability_items': liability_items,
            'liabilities_total': liabilities_total,
            'equity_items': equity_items,
            'equity_total': equity_total,
            'liability_and_equity_total': liabilities_total + equity_total,
        }


def filter_accounts(accounts, asset_type:AccountTypeEnum):
    return [{
        'display_name': v.display_name,
        'balance': float(v.balance())}
        for k, v in accounts.items()
        if v.account_type == asset_type]
