import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class WarrantyBase(BaseModel):
    provider: str | None = Field(default=None, max_length=150)
    expires_on: date
    policy_number: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)


class WarrantyCreate(WarrantyBase):
    pass


class WarrantyUpdate(BaseModel):
    provider: str | None = Field(default=None, max_length=150)
    expires_on: date | None = None
    policy_number: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)


class WarrantyRead(WarrantyBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_id: uuid.UUID


class ExpiringWarrantyRead(BaseModel):
    item_id: uuid.UUID
    item_name: str
    provider: str | None
    expires_on: date
    days_until_expiry: int


class WarrantyOverviewRead(WarrantyRead):
    item_name: str
    item_status: str
    days_until_expiry: int
