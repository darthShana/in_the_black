import logging

from langchain_core.tools import StructuredTool
from pydantic.v1 import Field, BaseModel

from my_agent.model.document import DocumentTypeEnum
log = logging.getLogger(__name__)


class ClassifyDocumentInput(BaseModel):
    document_path: str = Field(description="the path of the document")


def classify_document(document_path: str) -> (DocumentTypeEnum):
    log.info(f'Classifying document: {document_path}')
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
