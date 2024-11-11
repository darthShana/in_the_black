import json

from dateutil.relativedelta import relativedelta
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool

from my_agent.retrievers.company_insights import review_expenses
from my_agent.retrievers.accepted_anomalies import accepted_anomalies
from my_agent.retrievers.get_transactions import get_transactions
from my_agent.retrievers.get_user import UserRetriever
from my_agent.tools.company_overview import company_overview


def user_greeting(config: RunnableConfig):
    token = config.get("configurable", {}).get("access_token")
    user = UserRetriever.get_user(token)
    transactions = get_transactions(user_id=user.user_id, start=None, end=None)

    if not transactions:
        return """User has no transactions loaded, They can get started by 
        * uploading some statements with transactions by dragging them into file upload widget
        * connect to a bank account by pressing the connect to bank account widget 
        """

    last_transaction = max(transactions, key=lambda t: t.date)
    # Find the end date (last day of the current month)
    end_date = last_transaction.date.replace(day=1) + relativedelta(months=1, days=-1)
    # Find the start date (first day of the month 12 months before)
    start_date = last_transaction.date.replace(day=1) - relativedelta(months=11)
    overview = company_overview(config, start_date, end_date)
    anomalies = accepted_anomalies(user, start_date, end_date)
    overview['relevant_insights'] = {
        "expenses": review_expenses(overview['monthly_expenses'], anomalies)
    }
    return json.dumps(overview)


user_greeting_tool_name = "user_greeting"
user_greeting_tool = StructuredTool.from_function(
    func=user_greeting,
    name=user_greeting_tool_name,
    description="""
        Useful for providing a greeting for a returning user
        """,
)
