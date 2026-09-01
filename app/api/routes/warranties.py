import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status

from app.api.dependencies import CurrentUser, DbSession
from app.schemas.warranty import (
    ExpiringWarrantyRead,
    WarrantyCreate,
    WarrantyOverviewRead,
    WarrantyRead,
    WarrantyUpdate,
)
from app.services.inventory import get_item
from app.services.warranty import (
    ItemNotFoundError,
    WarrantyAlreadyExistsError,
    create_warranty,
    delete_warranty,
    get_warranty,
    list_expiring_within,
    list_warranties,
    update_warranty,
)

router = APIRouter(tags=["warranties"])


def _ensure_owned_item(db: DbSession, item_id: uuid.UUID, current_user: CurrentUser) -> None:
    if get_item(db, item_id, current_user.id) is None:
        raise HTTPException(status_code=404, detail="Item not found")


@router.post("/items/{item_id}/warranty", response_model=WarrantyRead, status_code=status.HTTP_201_CREATED)
def create_warranty_endpoint(
    item_id: uuid.UUID, payload: WarrantyCreate, db: DbSession, current_user: CurrentUser
) -> WarrantyRead:
    _ensure_owned_item(db, item_id, current_user)
    try:
        return create_warranty(db, item_id, payload)
    except ItemNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except WarrantyAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/items/{item_id}/warranty", response_model=WarrantyRead)
def get_warranty_endpoint(item_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> WarrantyRead:
    _ensure_owned_item(db, item_id, current_user)
    warranty = get_warranty(db, item_id)
    if warranty is None:
        raise HTTPException(status_code=404, detail="Warranty not found")
    return warranty


@router.patch("/items/{item_id}/warranty", response_model=WarrantyRead)
def update_warranty_endpoint(
    item_id: uuid.UUID, payload: WarrantyUpdate, db: DbSession, current_user: CurrentUser
) -> WarrantyRead:
    _ensure_owned_item(db, item_id, current_user)
    warranty = get_warranty(db, item_id)
    if warranty is None:
        raise HTTPException(status_code=404, detail="Warranty not found")
    return update_warranty(db, warranty, payload)


@router.delete("/items/{item_id}/warranty", status_code=status.HTTP_204_NO_CONTENT)
def delete_warranty_endpoint(item_id: uuid.UUID, db: DbSession, current_user: CurrentUser) -> None:
    _ensure_owned_item(db, item_id, current_user)
    warranty = get_warranty(db, item_id)
    if warranty is None:
        raise HTTPException(status_code=404, detail="Warranty not found")
    delete_warranty(db, warranty)


@router.get("/warranties", response_model=list[WarrantyOverviewRead])
def list_warranties_endpoint(db: DbSession, current_user: CurrentUser) -> list[WarrantyOverviewRead]:
    today = date.today()
    return [
        WarrantyOverviewRead(
            id=warranty.id,
            item_id=warranty.item_id,
            item_name=warranty.item.name,
            item_status=warranty.item.status,
            provider=warranty.provider,
            expires_on=warranty.expires_on,
            policy_number=warranty.policy_number,
            notes=warranty.notes,
            days_until_expiry=(warranty.expires_on - today).days,
        )
        for warranty in list_warranties(db, user_id=current_user.id)
    ]


@router.get("/warranties/expiring", response_model=list[ExpiringWarrantyRead])
def list_expiring_warranties_endpoint(
    db: DbSession,
    current_user: CurrentUser,
    within: int = Query(default=30),
) -> list[ExpiringWarrantyRead]:
    if within not in (30, 60, 90):
        raise HTTPException(status_code=422, detail="within must be one of 30, 60, or 90")

    today = date.today()
    return [
        ExpiringWarrantyRead(
            item_id=warranty.item_id,
            item_name=warranty.item.name,
            provider=warranty.provider,
            expires_on=warranty.expires_on,
            days_until_expiry=(warranty.expires_on - today).days,
        )
        for warranty in list_expiring_within(db, within, user_id=current_user.id)
    ]
