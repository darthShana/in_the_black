import re

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate, FewShotPromptWithTemplates
from langchain_core.utils.json import parse_json_markdown
from langsmith import traceable
from my_agent.retrievers.templates import transaction_classification_example_template, transaction_classification_prefix, transaction_classification_examples, \
    transaction_filter_example_template, transaction_filter_prefix, transaction_filter_examples

import logging

log = logging.getLogger(__name__)


available_transaction_types = [{
        "name": "loan_interest",
        "description": "interest paid on loans (mortgages) used for the rental properties"
    }, {
        "name": "rental_income",
        "description": "rental income received from rental properties"
    }, {
        "name": "water",
        "description": "payments made for water"
    }, {
       "name": "rates",
       "description": "payments made for council rates"
    }, {
       "name": "insurance",
       "description": "payments made for proprietary insurance"
    }, {
        "name": "capital withdrawal",
        "description": "funds taken out of the company account"
    }, {
        "name": "capital deposit",
        "description": "funds put into the company account"
    }, {
        "name": "unknown_payment",
        "description": "other payments made from this bank account"
    }, {
        "name": "unknown_deposit",
        "description": "other deposits made to this bank account"
    }]


class BankStatementRetriever:

    chat = ChatAnthropic(model="claude-3-5-sonnet-20240620")

    @staticmethod
    def escape_f_string(text):
        return text.replace('{', '{{').replace('}', '}}')

    @staticmethod
    def escape_examples(examples):
        return [{k: BankStatementRetriever.escape_f_string(v) for k, v in example.items()} for example in examples]

    CLASSIFICATION_EXAMPLE_PROMPT = PromptTemplate(
        input_variables=["transaction", "result"], template=transaction_classification_example_template
    )
    FILTER_EXAMPLE_PROMPT = PromptTemplate(
        input_variables=["transaction", "filter", 'result'], template=transaction_filter_example_template
    )

    @traceable
    def classify_transactions(self, transactions: list):
        prefix = PromptTemplate(
            input_variables=["transaction_types"], template=transaction_classification_prefix
        )
        suffix = PromptTemplate(
            input_variables=["transactions"],
            template="""
                            So given 
                            transactions: 
                            {{transactions}}. 
                            Extract the result in json format marking the json as ```json:""",
        )

        prompt = FewShotPromptWithTemplates(
            suffix=suffix,
            prefix=prefix,
            input_variables=["transaction_types", "transactions"],
            examples=BankStatementRetriever.escape_examples(transaction_classification_examples),
            example_prompt=self.CLASSIFICATION_EXAMPLE_PROMPT,
            example_separator="\n",
        )

        chain = prompt | self.chat
        output = []
        batch_size = 20
        for i in range(0, len(transactions), batch_size):
            out = chain.invoke({"transaction_types": available_transaction_types, "transactions": transactions[i:i + batch_size]})
            output.extend(parse_json_markdown(out.content))

        return output

    def filter_transactions(self, transactions: list, statement_filter):
        prefix = PromptTemplate(
            input_variables=[], template=transaction_filter_prefix
        )

        suffix = PromptTemplate(
            input_variables=["filter"],
            template="""
                                    So given 
                                    filter: 
                                    {{filter}}. 
                                    Extract the regex and respond in json format marking the json as ```json:""",
        )

        prompt = FewShotPromptWithTemplates(
            suffix=suffix,
            prefix=prefix,
            input_variables=["filter"],
            examples=BankStatementRetriever.escape_examples(transaction_filter_examples),
            example_prompt=self.FILTER_EXAMPLE_PROMPT,
            example_separator="\n",
        )

        chain = prompt | self.chat
        output = chain.invoke({"filter": statement_filter})
        regex = parse_json_markdown(output.content)['regex']
        log.info(regex)

        return [transaction for transaction in transactions
                if re.search(regex, ' '.join(f"{k}:{v}" for k, v in transaction.items()), re.IGNORECASE)]


