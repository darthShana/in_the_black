import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import StructuredTool
from langchain_core.utils.json import parse_json_markdown
from pydantic.v1 import Field, BaseModel

from my_agent.model.document import DocumentTypeEnum
from my_agent.retrievers.file_loader import AWSCSVFileLoader, AWSPDFFileLoader
from my_agent.retrievers.get_user import UserRetriever
from my_agent.utils.aws_credentials import AWSSessionFactory

log = logging.getLogger(__name__)
chat = ChatAnthropic(model="claude-3-5-sonnet-20240620")


class ClassifyDocumentInput(BaseModel):
    config: RunnableConfig = Field(description="runnable config")
    file_name: str = Field(description="the document to classify")


def classify_document(config: RunnableConfig, file_name: str) -> DocumentTypeEnum:
    aws = AWSSessionFactory()
    s3 = aws.get_session().client('s3')

    token = config.get("configurable", {}).get("access_token")
    user = UserRetriever.get_user(token)

    document_type_selection_prompt = """Given some document content, select the most appropriate document type from document types provided.
                Document types:
                bank_statement: a statement containing transactions from a bank with revenue going in as positive amounts and expenses going out as negative amounts"
                property_management_statement: a statement containing transactions from a property manager collecting rental revenue and paying expenses on the companies behalf"
                vendor_statement: a statement containing charges from a vendor with payments being made for a service"
                Extract the result in json format with the answer in property document_type, marking the json as ```json:
                """
    if file_name.endswith(".csv"):
        file_loader = AWSCSVFileLoader(
            client=s3,
            bucket="black-transactions-8e8f04a",
            key=f"{user.user_id}/{file_name}")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", document_type_selection_prompt),
                ("user", "document content: {document_content}")
            ]
        )
        chain = prompt | chat
        response = chain.invoke({"document_content": file_loader.load_head(20)})
        result = parse_json_markdown(response.content)

    else:
        file_loader = AWSPDFFileLoader(
            client=s3,
            bucket="black-transactions-8e8f04a",
            key=f"{user.user_id}/{file_name}")

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", document_type_selection_prompt),
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
        chain = prompt | chat
        response = chain.invoke({"image_data": file_loader.load_content()[0]})
        result = parse_json_markdown(response.content)

    if result['document_type'] == 'vendor_statement':
        return DocumentTypeEnum.VENDOR_STATEMENT
    elif result['document_type'] == 'property_management_statement':
        return DocumentTypeEnum.PROPERTY_MANAGEMENT_STATEMENT
    else:
        return DocumentTypeEnum.BANK_STATEMENT


document_classifier_tool_name = "document_classifier"
document_classifier_tool = StructuredTool.from_function(
    func=classify_document,
    name=document_classifier_tool_name,
    description="""
        Useful for finding what type of document has been uploaded so it can be processed
        """,
    args_schema=ClassifyDocumentInput,
)
