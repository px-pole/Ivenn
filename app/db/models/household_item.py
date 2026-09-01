import uuid
from datetime import date

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class HouseholdItem(Base):
    __tablename__ = "household_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    room_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rooms.id"))
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("categories.id"))

    name: Mapped[str] = mapped_column(String(200))
    brand: Mapped[str | None] = mapped_column(String(100), default=None)
    model: Mapped[str | None] = mapped_column(String(100), default=None)
    serial_number: Mapped[str | None] = mapped_column(String(100), default=None)
    estimated_value: Mapped[float | None] = mapped_column(Numeric(10, 2), default=None)
    purchase_date: Mapped[date | None] = mapped_column(default=None)
    status: Mapped[str] = mapped_column(String(20), default="active")

    owner: Mapped["User"] = relationship(back_populates="items")
    room: Mapped["Room"] = relationship(back_populates="items")
    category: Mapped["Category"] = relationship(back_populates="items")
    warranty: Mapped["Warranty | None"] = relationship(
        back_populates="item", uselist=False, cascade="all, delete-orphan"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="item", cascade="all, delete-orphan"
    )
