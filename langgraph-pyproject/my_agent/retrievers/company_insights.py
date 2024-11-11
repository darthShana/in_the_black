import logging

from langchain_core.prompts import PromptTemplate, FewShotPromptWithTemplates
from langchain_core.utils.json import parse_json_markdown
from langchain_anthropic import ChatAnthropic

from my_agent.retrievers.templates import expenses_insights_prefix, expenses_insights_examples, expenses_insights_example_template
from my_agent.retrievers.utils import escape_examples


log = logging.getLogger(__name__)
chat = ChatAnthropic(model="claude-3-5-sonnet-20240620", max_tokens=4096)


EXPENSES_INSIGHTS_EXAMPLE_PROMPT = PromptTemplate(
        input_variables=["monthly_breakdown", "accepted_anomalies", "result"], template=expenses_insights_example_template
    )


def review_expenses(monthly_expenses: list[dict], accepted_anomalies: list[dict]) -> dict:
    prefix = PromptTemplate(
        input_variables=[], template=expenses_insights_prefix
    )
    suffix = PromptTemplate(
        input_variables=["monthly_breakdown"],
        template="""
                                So given this 
                                monthly breakdown: 
                                {{monthly_breakdown}}.
                                accepted anomalies:
                                {{accepted_anomalies}}
                                Extract the result in json format marking the json as ```json:""",
    )

    prompt = FewShotPromptWithTemplates(
        suffix=suffix,
        prefix=prefix,
        input_variables=["monthly_breakdown", "accepted_anomalies"],
        examples=escape_examples(expenses_insights_examples),
        example_prompt=EXPENSES_INSIGHTS_EXAMPLE_PROMPT,
        example_separator="\n",
    )

    chain = prompt | chat
    out = chain.invoke({"monthly_breakdown": monthly_expenses, "accepted_anomalies": accepted_anomalies})
    log.info(out.content)
    return {
        'issues': parse_json_markdown(out.content)['issues'],
        'accepted_issues': accepted_anomalies
    }
