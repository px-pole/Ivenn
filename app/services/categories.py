import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Category, HouseholdItem
from app.schemas.category import CategoryCreate, CategoryUpdate


class DuplicateCategoryError(Exception):
    """Raised when a category with the same name already exists."""


class CategoryHasItemsError(Exception):
    """Raised when a category still contains inventory items."""


def create_category(db: Session, data: CategoryCreate) -> Category:
    category = Category(name=data.name)
    db.add(category)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateCategoryError(f"Category '{data.name}' already exists") from exc
    db.refresh(category)
    return category


def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)))


def get_category(db: Session, category_id: uuid.UUID) -> Category | None:
    return db.get(Category, category_id)


def update_category(db: Session, category: Category, data: CategoryUpdate) -> Category:
    category.name = data.name
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateCategoryError(f"Category '{data.name}' already exists") from exc
    db.refresh(category)
    return category


def delete_category(db: Session, category: Category) -> None:
    item_count = db.scalar(select(func.count(HouseholdItem.id)).where(HouseholdItem.category_id == category.id)) or 0
    if item_count:
        raise CategoryHasItemsError(
            f"Category '{category.name}' contains {item_count} item(s); move them before deleting it"
        )

    db.delete(category)
    db.commit()
