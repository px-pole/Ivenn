import uuid

from pydantic import BaseModel, ConfigDict, Field


class RoomBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class RoomCreate(RoomBase):
    pass


class RoomUpdate(RoomBase):
    pass


class RoomRead(RoomBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
