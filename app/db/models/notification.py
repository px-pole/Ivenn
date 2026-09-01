import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (UniqueConstraint("user_id", "dedup_key", name="uq_notifications_user_dedup_key"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(index=True)
    warranty_id: Mapped[uuid.UUID] = mapped_column(index=True)
    item_id: Mapped[uuid.UUID] = mapped_column(index=True)
    item_name: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(String(500))
    dedup_key: Mapped[str] = mapped_column(String(200))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
