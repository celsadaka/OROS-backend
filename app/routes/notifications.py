# app/routes/notifications.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from ..dependencies import get_db
from ..models.notification import notifications, Priority
from ..models.doctor import doctors

router = APIRouter()


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


class NotificationOut(BaseModel):
    id: int
    doctor_id: int
    title: str
    message: str
    priority: Priority
    is_read: bool
    related_entity_type: Optional[str] = None
    related_entity_id: Optional[int] = None
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def _ensure_doctor(db: Session, doctor_id: int):
    obj = db.get(doctors, doctor_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Doctor not found")


@router.post("/", response_model=NotificationOut, status_code=201)
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    _ensure_doctor(db, payload.doctor_id)
    obj = notifications(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=List[NotificationOut])
def list_notifications(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    doctor_id: Optional[int] = Query(None),
    is_read: Optional[bool] = Query(None),
    priority: Optional[Priority] = Query(None),
    related_entity_type: Optional[str] = Query(None),
    created_from: Optional[datetime] = Query(None),
    created_to: Optional[datetime] = Query(None),
    search: Optional[str] = Query(None, description="Search in title/message"),
):
    q = db.query(notifications)
    if doctor_id is not None:
        q = q.filter(notifications.doctor_id == doctor_id)
    if is_read is not None:
        q = q.filter(notifications.is_read == is_read)
    if priority is not None:
        q = q.filter(notifications.priority == priority)
    if related_entity_type:
        q = q.filter(notifications.related_entity_type == related_entity_type)
    if created_from is not None:
        q = q.filter(notifications.created_at >= created_from)
    if created_to is not None:
        q = q.filter(notifications.created_at <= created_to)
    if search:
        like = f"%{search}%"
        q = q.filter((notifications.title.ilike(like)) | (notifications.message.ilike(like)))
    return q.order_by(notifications.id.desc()).offset(offset).limit(limit).all()


@router.get("/{notification_id}", response_model=NotificationOut)
def get_notification(notification_id: int, db: Session = Depends(get_db)):
    obj = db.get(notifications, notification_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Notification not found")
    return obj


@router.patch("/{notification_id}", response_model=NotificationOut)
def update_notification(notification_id: int, payload: NotificationUpdate, db: Session = Depends(get_db)):
    obj = db.get(notifications, notification_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Notification not found")

    data = payload.model_dict(exclude_unset=True) if hasattr(payload, "model_dict") else payload.dict(exclude_unset=True)

    # If toggling read status and read_at not provided, set automatically
    if "is_read" in data and data["is_read"] and not data.get("read_at"):
        data["read_at"] = datetime.utcnow()

    for k, v in data.items():
        setattr(obj, k, v)

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{notification_id}", status_code=204)
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    obj = db.get(notifications, notification_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Notification not found")
    db.delete(obj)
    db.commit()
    return None


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    obj = db.get(notifications, notification_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Notification not found")
    if not obj.is_read:
        obj.is_read = True
        obj.read_at = datetime.utcnow()
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj
