import uuid
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AttachmentType(str, Enum):
    ITEM_PHOTO = "item_photo"
    RECEIPT = "receipt"
    WARRANTY_DOCUMENT = "warranty_document"
    OTHER = "other"


class AttachmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_id: uuid.UUID
    file_name: str
    mime_type: str
    attachment_type: AttachmentType


class ReceiptFieldSuggestion(BaseModel):
    value: str
    confidence: float = Field(ge=0, le=1)
    evidence: str


class ReceiptExtractionRead(BaseModel):
    raw_text: str
    merchant: ReceiptFieldSuggestion | None = None
    purchase_date: ReceiptFieldSuggestion | None = None
    estimated_value: ReceiptFieldSuggestion | None = None
    model: ReceiptFieldSuggestion | None = None
    serial_number: ReceiptFieldSuggestion | None = None
