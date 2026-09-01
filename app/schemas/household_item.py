import uuid
from datetime import date
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ItemStatus(str, Enum):
    ACTIVE = "active"
    SOLD = "sold"
    DONATED = "donated"
    DISPOSED = "disposed"


class HouseholdItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    room_id: uuid.UUID
    category_id: uuid.UUID
    brand: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    estimated_value: Decimal | None = Field(default=None, ge=0)
    purchase_date: date | None = None


class HouseholdItemCreate(HouseholdItemBase):
    user_id: uuid.UUID | None = None


class HouseholdItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    room_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    brand: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    serial_number: str | None = Field(default=None, max_length=100)
    estimated_value: Decimal | None = Field(default=None, ge=0)
    purchase_date: date | None = None


class HouseholdItemStatusUpdate(BaseModel):
    status: ItemStatus


class HouseholdItemRead(HouseholdItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    status: ItemStatus
