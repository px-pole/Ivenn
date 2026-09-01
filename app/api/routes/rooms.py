import uuid

from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencies import DbSession
from app.schemas.room import RoomCreate, RoomRead, RoomUpdate
from app.services.rooms import (
    DuplicateRoomError,
    RoomHasItemsError,
    create_room,
    delete_room,
    get_room,
    list_rooms,
    update_room,
)

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.post("", response_model=RoomRead, status_code=status.HTTP_201_CREATED)
def create_room_endpoint(payload: RoomCreate, db: DbSession) -> RoomRead:
    try:
        return create_room(db, payload)
    except DuplicateRoomError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[RoomRead])
def list_rooms_endpoint(db: DbSession) -> list[RoomRead]:
    return list_rooms(db)


@router.get("/{room_id}", response_model=RoomRead)
def get_room_endpoint(room_id: uuid.UUID, db: DbSession) -> RoomRead:
    room = get_room(db, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


@router.patch("/{room_id}", response_model=RoomRead)
def update_room_endpoint(room_id: uuid.UUID, payload: RoomUpdate, db: DbSession) -> RoomRead:
    room = get_room(db, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    try:
        return update_room(db, room, payload)
    except DuplicateRoomError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_room_endpoint(room_id: uuid.UUID, db: DbSession) -> Response:
    room = get_room(db, room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    try:
        delete_room(db, room)
    except RoomHasItemsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
