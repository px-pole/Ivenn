import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.notification import NotificationCountRead, NotificationRead, NotificationUpdate
from app.services.notifications import get_notification, list_notifications, mark_all_read, update_notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
def list_notifications_endpoint(db: DbSession, current_user: CurrentUser) -> list[NotificationRead]:
    return list_notifications(db, current_user.id)


@router.patch("/{notification_id}", response_model=NotificationRead)
def update_notification_endpoint(
    notification_id: uuid.UUID,
    payload: NotificationUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> NotificationRead:
    notification = get_notification(db, notification_id, current_user.id)
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return update_notification(
        db,
        notification,
        is_read=payload.is_read,
        is_dismissed=payload.is_dismissed,
    )


@router.post("/mark-all-read", response_model=NotificationCountRead)
def mark_all_read_endpoint(db: DbSession, current_user: CurrentUser) -> NotificationCountRead:
    return NotificationCountRead(updated_count=mark_all_read(db, current_user.id))
