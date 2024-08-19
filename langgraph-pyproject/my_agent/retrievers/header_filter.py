import pandas as pd
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate, FewShotPromptWithTemplates
from langchain_core.utils.json import parse_json_markdown

from my_agent.retrievers.bank_statement_retriever import BankStatementRetriever
from my_agent.retrievers.file_loader import FileLoader
from my_agent.retrievers.templates import header_filter_example_template, header_filter_examples, header_filter_prefix


class HeaderFilter:

    chat = ChatAnthropic(model="claude-3-5-sonnet-20240620")

    EXAMPLE_PROMPT2 = PromptTemplate(
        input_variables=["content", "result"], template=header_filter_example_template
    )

    def __init__(self, file_loader: FileLoader):
        self.file_loader = file_loader

    def extract_transactions(self):
        f = self.lines_to_skip()
        return self.file_loader.load_data_frame(f['line_number'])

    def lines_to_skip(self):
        head = self.file_loader.load_head(20)

        prefix = PromptTemplate(
            input_variables=[], template=header_filter_prefix
        )
        suffix = PromptTemplate(
            input_variables=["content"],
            template="""
                    So given 
                    Content: 
                    {content}. 
                    Extract the result in json format marking the json as ```json:""",
        )

        prompt = FewShotPromptWithTemplates(
            suffix=suffix,
            prefix=prefix,
            input_variables=["content"],
            examples=BankStatementRetriever.escape_examples(header_filter_examples),
            example_prompt=self.EXAMPLE_PROMPT2,
            example_separator="\n",
        )

        chain = prompt | self.chat
        output = chain.invoke({"content": head})

        return parse_json_markdown(output.content)

