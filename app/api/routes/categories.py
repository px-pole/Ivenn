import uuid

from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import DbSession
from app.schemas.category import CategoryCreate, CategoryRead, CategoryUpdate
from app.services.categories import (
    CategoryHasItemsError,
    DuplicateCategoryError,
    create_category,
    delete_category,
    get_category,
    list_categories,
    update_category,
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category_endpoint(payload: CategoryCreate, db: DbSession) -> CategoryRead:
    try:
        return create_category(db, payload)
    except DuplicateCategoryError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[CategoryRead])
def list_categories_endpoint(db: DbSession) -> list[CategoryRead]:
    return list_categories(db)


@router.get("/{category_id}", response_model=CategoryRead)
def get_category_endpoint(category_id: uuid.UUID, db: DbSession) -> CategoryRead:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category_endpoint(category_id: uuid.UUID, payload: CategoryUpdate, db: DbSession) -> CategoryRead:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    try:
        return update_category(db, category, payload)
    except DuplicateCategoryError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category_endpoint(category_id: uuid.UUID, db: DbSession) -> Response:
    category = get_category(db, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    try:
        delete_category(db, category)
    except CategoryHasItemsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
