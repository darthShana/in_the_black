import logging
from typing import Dict

import chevron

from my_agent.model.account import Account, AccountTypeEnum

log = logging.getLogger(__name__)


def generate_statement_of_profit_or_loss(accounts: Dict[str, Account]) -> dict:
    revenue_items = [{
        'display_name': v.display_name,
        'balance': float(v.balance())}
        for k, v in accounts.items()
        if v.account_type == AccountTypeEnum.REVENUE]
    revenue_total = sum(account['balance'] for account in revenue_items)

    expenses_items = [{
        'display_name': v.display_name,
        'balance': float(v.balance())}
        for k, v in accounts.items()
        if v.account_type == AccountTypeEnum.EXPENSES]
    expenses_total = sum(account['balance'] for account in expenses_items)

    with open('my_agent/generators/mustache/statement_of_profit_or_loss.mustache', 'r') as f:
        result = chevron.render(f, {
            'revenue_items': revenue_items,
            'gross_profit': revenue_total,
            'expenses_items': expenses_items,
            'expenses_total': expenses_total
        })
        log.info(result)
    return {
            'revenue_items': revenue_items,
            'gross_profit': revenue_total,
            'expenses_items': expenses_items,
            'expenses_total': expenses_total
        }
