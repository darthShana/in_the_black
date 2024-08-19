from enum import Enum


class DocumentTypeEnum(str, Enum):
    BANK_STATEMENT = 'bank_statement'
    BILL = 'bill'
