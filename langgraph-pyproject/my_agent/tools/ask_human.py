from enum import Enum
from typing import List

from pydantic.v1 import BaseModel, Field


class QuestionType(str, Enum):
    CONFIRMATION = 'confirmation'
    MULTI_CHOICE = 'multi_choice'
    FREE_FORM = 'free_form'


class AskHuman(BaseModel):
    """Ask the human a question"""
    question: str = Field(description='the question to ask')
    question_type: QuestionType = Field(description="if the question response is one of confirmation, selection of one option or free text response")
    options: List[str] = Field(description="list of available options for multi-choice questions")
