import uuid
from datetime import date
from typing import Literal

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.storage import delete_file
from app.db.models import Category, HouseholdItem, Room, Warranty
from app.schemas.household_item import HouseholdItemCreate, HouseholdItemUpdate, ItemStatus

WarrantyStatusFilter = Literal["active", "expired", "none"]


class InvalidReferenceError(Exception):
    """Raised when a referenced room or category does not exist."""


def _ensure_room_and_category_exist(db: Session, *, room_id: uuid.UUID, category_id: uuid.UUID) -> None:
    if db.get(Room, room_id) is None:
        raise InvalidReferenceError(f"Room {room_id} does not exist")
    if db.get(Category, category_id) is None:
        raise InvalidReferenceError(f"Category {category_id} does not exist")


def create_item(db: Session, data: HouseholdItemCreate, user_id: uuid.UUID | None = None) -> HouseholdItem:
    resolved_user_id = user_id if user_id is not None else getattr(data, "user_id", None)
    if resolved_user_id is None:
        raise ValueError("user_id is required")

    _ensure_room_and_category_exist(db, room_id=data.room_id, category_id=data.category_id)

    item = HouseholdItem(
        user_id=resolved_user_id,
        room_id=data.room_id,
        category_id=data.category_id,
        name=data.name,
        brand=data.brand,
        model=data.model,
        serial_number=data.serial_number,
        estimated_value=data.estimated_value,
        purchase_date=data.purchase_date,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def get_item(db: Session, item_id: uuid.UUID, user_id: uuid.UUID | None = None) -> HouseholdItem | None:
    stmt = select(HouseholdItem).where(HouseholdItem.id == item_id)
    if user_id is not None:
        stmt = stmt.where(HouseholdItem.user_id == user_id)
    return db.scalars(stmt).first()


def list_items(
    db: Session,
    *,
    user_id: uuid.UUID | None = None,
    room_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    status: ItemStatus | None = None,
    warranty_status: WarrantyStatusFilter | None = None,
    search: str | None = None,
) -> list[HouseholdItem]:
    stmt = select(HouseholdItem).outerjoin(HouseholdItem.warranty)

    if user_id is not None:
        stmt = stmt.where(HouseholdItem.user_id == user_id)

    if room_id is not None:
        stmt = stmt.where(HouseholdItem.room_id == room_id)
    if category_id is not None:
        stmt = stmt.where(HouseholdItem.category_id == category_id)
    if status is not None:
        stmt = stmt.where(HouseholdItem.status == status.value)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                HouseholdItem.name.ilike(pattern),
                HouseholdItem.brand.ilike(pattern),
                HouseholdItem.model.ilike(pattern),
                HouseholdItem.serial_number.ilike(pattern),
            )
        )
    if warranty_status == "none":
        stmt = stmt.where(Warranty.id.is_(None))
    elif warranty_status == "active":
        stmt = stmt.where(Warranty.expires_on.is_not(None), Warranty.expires_on >= date.today())
    elif warranty_status == "expired":
        stmt = stmt.where(Warranty.expires_on.is_not(None), Warranty.expires_on < date.today())

    stmt = stmt.order_by(HouseholdItem.name)
    return list(db.scalars(stmt))


def update_item(db: Session, item: HouseholdItem, data: HouseholdItemUpdate) -> HouseholdItem:
    updates = data.model_dump(exclude_unset=True)

    if "room_id" in updates or "category_id" in updates:
        _ensure_room_and_category_exist(
            db,
            room_id=updates.get("room_id", item.room_id),
            category_id=updates.get("category_id", item.category_id),
        )

    for field, value in updates.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


def set_item_status(db: Session, item: HouseholdItem, new_status: ItemStatus) -> HouseholdItem:
    item.status = new_status.value
    db.commit()
    db.refresh(item)
    return item


def delete_item(db: Session, item: HouseholdItem) -> None:
    storage_keys = [attachment.storage_key for attachment in item.attachments]
    db.delete(item)
    db.commit()
    for storage_key in storage_keys:
        delete_file(storage_key)
