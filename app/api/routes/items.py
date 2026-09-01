import uuid

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.dependencies import CurrentUser, DbSession, require_same_user_scope
from app.schemas.household_item import (
    HouseholdItemCreate,
    HouseholdItemRead,
    HouseholdItemStatusUpdate,
    HouseholdItemUpdate,
    ItemStatus,
)
from app.services.inventory import (
    InvalidReferenceError,
    WarrantyStatusFilter,
    create_item,
    delete_item,
    get_item,
    list_items,
    set_item_status,
    update_item,
)

router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=HouseholdItemRead, status_code=status.HTTP_201_CREATED)
def create_item_endpoint(payload: HouseholdItemCreate, db: DbSession, current_user: CurrentUser) -> HouseholdItemRead:
    scope_user_id = require_same_user_scope(current_user, payload.user_id)
    try:
        return create_item(db, payload, scope_user_id)
    except InvalidReferenceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("", response_model=list[HouseholdItemRead])
def list_items_endpoint(
    db: DbSession,
    current_user: CurrentUser,
    user_id: uuid.UUID | None = Query(default=None),
    room_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    status_filter: ItemStatus | None = Query(default=None, alias="status"),
    warranty_status: WarrantyStatusFilter | None = None,
    search: str | None = Query(default=None, min_length=1, max_length=200),
) -> list[HouseholdItemRead]:
    scope_user_id = require_same_user_scope(current_user, user_id)
    return list_items(
        db,
        user_id=scope_user_id,
        room_id=room_id,
        category_id=category_id,
        status=status_filter,
        warranty_status=warranty_status,
        search=search,
    )


@router.get("/{item_id}", response_model=HouseholdItemRead)
def get_item_endpoint(
    item_id: uuid.UUID, db: DbSession, current_user: CurrentUser, user_id: uuid.UUID | None = Query(default=None)
) -> HouseholdItemRead:
    scope_user_id = require_same_user_scope(current_user, user_id)
    item = get_item(db, item_id, scope_user_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


@router.patch("/{item_id}", response_model=HouseholdItemRead)
def update_item_endpoint(
    item_id: uuid.UUID, payload: HouseholdItemUpdate, db: DbSession, current_user: CurrentUser, user_id: uuid.UUID | None = Query(default=None)
) -> HouseholdItemRead:
    scope_user_id = require_same_user_scope(current_user, user_id)
    item = get_item(db, item_id, scope_user_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    try:
        return update_item(db, item, payload)
    except InvalidReferenceError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/{item_id}/status", response_model=HouseholdItemRead)
def update_item_status_endpoint(
    item_id: uuid.UUID, payload: HouseholdItemStatusUpdate, db: DbSession, current_user: CurrentUser, user_id: uuid.UUID | None = Query(default=None)
) -> HouseholdItemRead:
    scope_user_id = require_same_user_scope(current_user, user_id)
    item = get_item(db, item_id, scope_user_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return set_item_status(db, item, payload.status)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item_endpoint(
    item_id: uuid.UUID, db: DbSession, current_user: CurrentUser, user_id: uuid.UUID | None = Query(default=None)
) -> Response:
    scope_user_id = require_same_user_scope(current_user, user_id)
    item = get_item(db, item_id, scope_user_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    delete_item(db, item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

