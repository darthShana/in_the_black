from typing import Union

import pandas as pd
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate, FewShotPromptWithTemplates, ChatPromptTemplate
from langchain_core.utils.json import parse_json_markdown
from langsmith import traceable

from my_agent.model.transaction import available_transaction_types
from my_agent.retrievers.templates import transaction_classification_example_template, transaction_classification_prefix, transaction_classification_examples

import logging

from my_agent.retrievers.utils import escape_examples

log = logging.getLogger(__name__)


class TransactionRetriever:

    chat = ChatAnthropic(model="claude-3-5-sonnet-20240620", max_tokens=4096)

    CLASSIFICATION_EXAMPLE_PROMPT = PromptTemplate(
        input_variables=["transaction", "result"], template=transaction_classification_example_template
    )

    statement_extraction_prefix = """
        You are a book keeper for a residential rental company. Extract a list of transactions present in statement.
        Produce the list where each element has all fields, do NOT group them
        Extract the result in json format marking the json as ```json:"""

    def extract_transactions(self, content: Union[list[str], pd.DataFrame]) -> list[dict]:
        if isinstance(content, list):
            return self._extract_from_image(content)
        elif isinstance(content, pd.DataFrame):
            return self._extract_from_dataframe(content)
        else:
            raise ValueError("Input must be either a string or a pandas DataFrame")

    def _extract_from_image(self, images_base64: list[str]) -> list[dict]:
        log.info(f"loaded images: {len(images_base64)}")

        images_prompt = []
        images_data = {}

        counter = 1
        for image in images_base64:
            images_prompt.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{{image_data{counter}}}"}
            })
            images_data[f"image_data{counter}"] = image
            counter = counter + 1

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.statement_extraction_prefix),
                (
                    "user", images_prompt
                ),
            ]
        )
        chain = prompt | self.chat
        response = chain.invoke(images_data)
        log.info(response)

        transactions = []
        markdown = parse_json_markdown(response.content)
        transactions.extend(markdown)
        return transactions


    def _extract_from_dataframe(self, data_frame: pd.DataFrame) -> list[dict]:
        return data_frame.to_dict("records")

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
            examples=escape_examples(transaction_classification_examples),
            example_prompt=self.CLASSIFICATION_EXAMPLE_PROMPT,
            example_separator="\n",
        )

        chain = prompt | self.chat
        output = []
        batch_size = 80
        for i in range(0, len(transactions), batch_size):
            out = chain.invoke({"transaction_types": available_transaction_types, "transactions": transactions[i:i + batch_size]})
            parsed_result = parse_json_markdown(out.content)
            if isinstance(parsed_result, list):
                output.extend(parsed_result)
            else:
                output.append(parsed_result)

        return output

    def classify_image(self, image: str):
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", """
                Given the following image of a Vendor statement for a residential property, select the service which the vendor is providing from the services provided
                Services: ['water', 'rates', 'insurance', 'property management', 'property maintenance']
                Extract the result in json format with the answer in property selected_service, marking the json as ```json:
                """
                 ),
                (
                    "user", [
                        {
                            "type": "image_url",
                            "image_url": {"url": "data:image/jpeg;base64,{image_data}"},
                        }
                    ]

                ),
            ]
        )
        chain = prompt | self.chat
        response = chain.invoke({"image_data": image})
        return parse_json_markdown(response.content)
