from enum import Enum


class DocumentTypeEnum(str, Enum):
    BANK_STATEMENT = 'bank_statement'
    VENDOR_STATEMENT = 'vendor_statement'
    PROPERTY_MANAGEMENT_STATEMENT = 'property_management_statement'
