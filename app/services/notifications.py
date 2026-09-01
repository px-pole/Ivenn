import uuid
from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Notification, Warranty
from app.services.warranty import list_expiring_within

REMINDER_WINDOWS: tuple[int, ...] = (30, 60, 90)


def _window_for(days_left: int) -> int:
    return next(window for window in REMINDER_WINDOWS if days_left <= window)


def sync_warranty_notifications(db: Session, user_id: uuid.UUID) -> int:
    warranties = list_expiring_within(db, max(REMINDER_WINDOWS), user_id=user_id)
    existing = list(db.scalars(select(Notification).where(Notification.user_id == user_id)))
    valid_warranty_ids = set(db.scalars(select(Warranty.id)))
    for notification in existing:
        if notification.warranty_id not in valid_warranty_ids:
            db.delete(notification)

    existing_keys = {notification.dedup_key for notification in existing}
    created = 0
    today = date.today()
    for warranty in warranties:
        days_left = (warranty.expires_on - today).days
        window = _window_for(days_left)
        dedup_key = f"warranty:{warranty.id}:{window}"
        if dedup_key in existing_keys:
            continue
        db.add(
            Notification(
                user_id=user_id,
                warranty_id=warranty.id,
                item_id=warranty.item_id,
                item_name=warranty.item.name,
                title="Warranty expiring soon",
                message=f"{warranty.item.name} expires in {days_left} day(s) on {warranty.expires_on.isoformat()}",
                dedup_key=dedup_key,
            )
        )
        existing_keys.add(dedup_key)
        created += 1
    db.commit()
    return created


def list_notifications(db: Session, user_id: uuid.UUID) -> list[Notification]:
    sync_warranty_notifications(db, user_id)
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id, Notification.is_dismissed.is_(False))
        .order_by(Notification.created_at.desc())
    )
    return list(db.scalars(stmt))


def get_notification(db: Session, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification | None:
    return db.scalar(select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id))


def update_notification(
    db: Session,
    notification: Notification,
    *,
    is_read: bool | None,
    is_dismissed: bool | None,
) -> Notification:
    if is_read is not None:
        notification.is_read = is_read
    if is_dismissed is not None:
        notification.is_dismissed = is_dismissed
    db.commit()
    db.refresh(notification)
    return notification


def mark_all_read(db: Session, user_id: uuid.UUID) -> int:
    notifications = list(
        db.scalars(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
                Notification.is_dismissed.is_(False),
            )
        )
    )
    for notification in notifications:
        notification.is_read = True
    db.commit()
    return len(notifications)
