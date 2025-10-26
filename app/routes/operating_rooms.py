# app/routes/operating_rooms.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from ..dependencies import get_db
from ..models.operating_room import operating_rooms, RoomStatus

router = APIRouter()


class OperatingRoomCreate(BaseModel):
    room_number: str
    room_name: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[RoomStatus] = RoomStatus.available
    location: Optional[str] = None


class OperatingRoomUpdate(BaseModel):
    room_number: Optional[str] = None
    room_name: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[RoomStatus] = None
    location: Optional[str] = None


class OperatingRoomOut(BaseModel):
    id: int
    room_number: str
    room_name: Optional[str] = None
    capacity: Optional[int] = None
    status: RoomStatus
    location: Optional[str] = None

    class Config:
        from_attributes = True


def _ensure_unique_room_number(db: Session, room_number: str, exclude_id: Optional[int] = None):
    q = db.query(operating_rooms).filter(operating_rooms.room_number == room_number)
    if exclude_id is not None:
        q = q.filter(operating_rooms.id != exclude_id)
    if db.query(q.exists()).scalar():
        raise HTTPException(status_code=400, detail="room_number already exists")


@router.post("/", response_model=OperatingRoomOut, status_code=201)
def create_operating_room(payload: OperatingRoomCreate, db: Session = Depends(get_db)):
    _ensure_unique_room_number(db, payload.room_number)
    obj = operating_rooms(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=List[OperatingRoomOut])
def list_operating_rooms(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[RoomStatus] = Query(None),
    capacity_min: Optional[int] = Query(None),
    capacity_max: Optional[int] = Query(None),
    search: Optional[str] = Query(None, description="Search room_number / room_name / location"),
):
    q = db.query(operating_rooms)
    if status is not None:
        q = q.filter(operating_rooms.status == status)
    if capacity_min is not None:
        q = q.filter(operating_rooms.capacity >= capacity_min)
    if capacity_max is not None:
        q = q.filter(operating_rooms.capacity <= capacity_max)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (operating_rooms.room_number.ilike(like)) |
            (operating_rooms.room_name.ilike(like)) |
            (operating_rooms.location.ilike(like))
        )
    return q.order_by(operating_rooms.id.desc()).offset(offset).limit(limit).all()


@router.get("/{room_id}", response_model=OperatingRoomOut)
def get_operating_room(room_id: int, db: Session = Depends(get_db)):
    obj = db.get(operating_rooms, room_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Operating room not found")
    return obj


@router.patch("/{room_id}", response_model=OperatingRoomOut)
def update_operating_room(room_id: int, payload: OperatingRoomUpdate, db: Session = Depends(get_db)):
    obj = db.get(operating_rooms, room_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Operating room not found")

    data = payload.model_dict(exclude_unset=True) if hasattr(payload, "model_dict") else payload.dict(exclude_unset=True)

    if "room_number" in data and data["room_number"]:
        _ensure_unique_room_number(db, data["room_number"], exclude_id=room_id)

    for k, v in data.items():
        setattr(obj, k, v)

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{room_id}", status_code=204)
def delete_operating_room(room_id: int, db: Session = Depends(get_db)):
    obj = db.get(operating_rooms, room_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Operating room not found")
    db.delete(obj)
    db.commit()
    return None
