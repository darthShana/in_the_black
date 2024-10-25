import logging
from datetime import datetime

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate, FewShotPromptWithTemplates
from langchain_core.tools import StructuredTool
from langchain_core.utils.json import parse_json_markdown
from pydantic.v1 import BaseModel, Field

from my_agent.retrievers.utils import escape_examples
from my_agent.retrievers.get_accounts import monthly_expenses
from my_agent.tools.templates import expense_validation_prefix, expense_validation_examples, expense_validation_example_template

log = logging.getLogger(__name__)
chat = ChatAnthropic(model="claude-3-5-sonnet-20240620", max_tokens=4096)

EXPENSE_VALIDATION_EXAMPLE_PROMPT = PromptTemplate(
    input_variables=["monthly_expenses", "results"], template=expense_validation_example_template
)


class ReviewAccountsInput(BaseModel):
    start_date: datetime = Field(description="review accounts starting from this date")
    end_date: datetime = Field(description="review accounts until and including this date")


def review_accounts(start_date: datetime, end_date: datetime):
    expenses = monthly_expenses(start_date, end_date)
    log.info('expenses')
    log.info(expenses)

    prefix = PromptTemplate(
        input_variables=["monthly_expenses"], template=expense_validation_prefix
    )
    suffix = PromptTemplate(
        input_variables=["monthly_expenses"],
        template="""
                                So given 
                                Monthly Expenses: 
                                {{monthly_expenses}}. 
                                Review them and generate the results in json format marking the json as ```json:""",
    )

    prompt = FewShotPromptWithTemplates(
        suffix=suffix,
        prefix=prefix,
        input_variables=["monthly_expenses"],
        examples=escape_examples(expense_validation_examples),
        example_prompt=EXPENSE_VALIDATION_EXAMPLE_PROMPT,
        example_separator="\n",
    )

    chain = prompt | chat
    out = chain.invoke({"monthly_expenses": expenses})
    parsed_result = parse_json_markdown(out.content)
    log.info('parsed_result')
    log.info(parsed_result)
    return parsed_result


review_accounts_tool_name = "review_accounts"
review_accounts_tool = StructuredTool.from_function(
    func=review_accounts,
    name=review_accounts_tool_name,
    description="""
        Useful to review accounts for a certain period to find possible issues and anomalies
        """,
    args_schema=ReviewAccountsInput,
)




