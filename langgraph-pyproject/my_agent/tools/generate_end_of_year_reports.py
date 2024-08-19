from typing import List, Dict

from my_agent.generators.statement_of_profit_or_loss import generate_statement_of_profit_or_loss
from my_agent.model.account import Account


def generate_end_of_year_reports(accounts: Dict[str, Account]) -> Dict[str, str]:
    statement_of_profit_or_loss = generate_statement_of_profit_or_loss(accounts)
    return {
        "statement_of_profit_or_loss": statement_of_profit_or_loss
    }
