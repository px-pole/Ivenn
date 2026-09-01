import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import HouseholdItem, Room
from app.schemas.room import RoomCreate, RoomUpdate


class DuplicateRoomError(Exception):
    """Raised when a room with the same name already exists."""


class RoomHasItemsError(Exception):
    """Raised when a room still contains inventory items."""


def create_room(db: Session, data: RoomCreate) -> Room:
    room = Room(name=data.name)
    db.add(room)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateRoomError(f"Room '{data.name}' already exists") from exc
    db.refresh(room)
    return room


def list_rooms(db: Session) -> list[Room]:
    return list(db.scalars(select(Room).order_by(Room.name)))


def get_room(db: Session, room_id: uuid.UUID) -> Room | None:
    return db.get(Room, room_id)


def update_room(db: Session, room: Room, data: RoomUpdate) -> Room:
    room.name = data.name
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateRoomError(f"Room '{data.name}' already exists") from exc
    db.refresh(room)
    return room


def delete_room(db: Session, room: Room) -> None:
    item_count = db.scalar(select(func.count(HouseholdItem.id)).where(HouseholdItem.room_id == room.id)) or 0
    if item_count:
        raise RoomHasItemsError(f"Room '{room.name}' contains {item_count} item(s); move them before deleting it")

    db.delete(room)
    db.commit()
