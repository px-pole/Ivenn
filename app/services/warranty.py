import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import HouseholdItem, Warranty
from app.schemas.household_item import ItemStatus
from app.schemas.warranty import WarrantyCreate, WarrantyUpdate


class ItemNotFoundError(Exception):
    """Raised when the household item does not exist."""


class WarrantyAlreadyExistsError(Exception):
    """Raised when the item already has a warranty record."""


def create_warranty(db: Session, item_id: uuid.UUID, data: WarrantyCreate) -> Warranty:
    item = db.get(HouseholdItem, item_id)
    if item is None:
        raise ItemNotFoundError(f"Item {item_id} does not exist")
    if item.warranty is not None:
        raise WarrantyAlreadyExistsError(f"Item {item_id} already has a warranty")

    warranty = Warranty(
        item_id=item_id,
        provider=data.provider,
        expires_on=data.expires_on,
        policy_number=data.policy_number,
        notes=data.notes,
    )
    db.add(warranty)
    db.commit()
    db.refresh(warranty)
    return warranty


def get_warranty(db: Session, item_id: uuid.UUID) -> Warranty | None:
    item = db.get(HouseholdItem, item_id)
    return item.warranty if item is not None else None


def update_warranty(db: Session, warranty: Warranty, data: WarrantyUpdate) -> Warranty:
    updates = data.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(warranty, field, value)

    db.commit()
    db.refresh(warranty)
    return warranty


def delete_warranty(db: Session, warranty: Warranty) -> None:
    db.delete(warranty)
    db.commit()


def list_warranties(db: Session, *, user_id: uuid.UUID | None = None) -> list[Warranty]:
    stmt = select(Warranty).join(Warranty.item).order_by(Warranty.expires_on, HouseholdItem.name)
    if user_id is not None:
        stmt = stmt.where(HouseholdItem.user_id == user_id)
    return list(db.scalars(stmt))


def list_expiring_within(db: Session, days: int, *, user_id: uuid.UUID | None = None) -> list[Warranty]:
    today = date.today()
    horizon = today + timedelta(days=days)
    stmt = (
        select(Warranty)
        .join(Warranty.item)
        .where(
            Warranty.expires_on >= today,
            Warranty.expires_on <= horizon,
            HouseholdItem.status == ItemStatus.ACTIVE.value,
        )
        .order_by(Warranty.expires_on)
    )
    if user_id is not None:
        stmt = stmt.where(HouseholdItem.user_id == user_id)
    return list(db.scalars(stmt))
