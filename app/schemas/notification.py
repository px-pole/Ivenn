import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_id: uuid.UUID
    item_name: str
    title: str
    message: str
    is_read: bool
    created_at: datetime


class NotificationUpdate(BaseModel):
    is_read: bool | None = None
    is_dismissed: bool | None = None


class NotificationCountRead(BaseModel):
    updated_count: int
