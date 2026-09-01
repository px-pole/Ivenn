import uuid
from datetime import date

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Warranty(Base):
    __tablename__ = "warranties"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("household_items.id"), unique=True)

    provider: Mapped[str | None] = mapped_column(String(150), default=None)
    expires_on: Mapped[date] = mapped_column()
    policy_number: Mapped[str | None] = mapped_column(String(100), default=None)
    notes: Mapped[str | None] = mapped_column(String(1000), default=None)

    item: Mapped["HouseholdItem"] = relationship(back_populates="warranty")
