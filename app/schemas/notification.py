from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.notification import Priority
from .common import ORMBase, WithTimestamps


class NotificationBase(ORMBase):
    doctor_id: int
    title: str
    message: str
    priority: Priority = Priority.low
    is_read: bool = False
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    read_at: Optional[datetime] = None


class NotificationCreate(BaseModel):
    doctor_id: int
    title: str
    message: str
    priority: Optional[Priority] = Priority.low
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None


class NotificationUpdate(BaseModel):
    title: Optional[str] = None
    message: Optional[str] = None
    priority: Optional[Priority] = None
    is_read: Optional[bool] = None
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    read_at: Optional[datetime] = None


class NotificationOut(NotificationBase, WithTimestamps):
    id: int

    class Config:
        from_attributes = True
