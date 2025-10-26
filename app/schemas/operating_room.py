from pydantic import BaseModel
from typing import Optional
from ..models.operating_room import RoomStatus
from .common import ORMBase, WithTimestamps


class OperatingRoomBase(ORMBase):
    room_number: str
    room_name: Optional[str] = None
    capacity: Optional[int] = None
    status: RoomStatus = RoomStatus.available
    location: Optional[str] = None

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


class OperatingRoomOut(OperatingRoomBase, WithTimestamps):
    id: int

    class Config:
        from_attributes = True
