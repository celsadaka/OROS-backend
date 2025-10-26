# app/routes/surgeries.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

from ..dependencies import get_db
from ..models.surgery import surgeries, SurgeryStatus
from ..models.patient import patients
from ..models.doctor import doctors
from ..models.operating_room import operating_rooms

router = APIRouter()


class SurgeryCreate(BaseModel):
    patient_id: int
    doctor_id: int
    operating_room_id: Optional[int] = None

    surgery_type: Optional[str] = None
    procedure_name: Optional[str] = None

    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None  # per ERD (e.g., "14:30")
    duration_minutes: Optional[int] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None

    status: Optional[SurgeryStatus] = SurgeryStatus.scheduled
    urgency_level: Optional[int] = None

    participants: Optional[str] = None
    pre_op_notes: Optional[str] = None
    post_op_notes: Optional[str] = None
    complications: Optional[str] = None


class SurgeryUpdate(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    operating_room_id: Optional[int] = None

    surgery_type: Optional[str] = None
    procedure_name: Optional[str] = None

    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None

    status: Optional[SurgeryStatus] = None
    urgency_level: Optional[int] = None

    participants: Optional[str] = None
    pre_op_notes: Optional[str] = None
    post_op_notes: Optional[str] = None
    complications: Optional[str] = None


class SurgeryOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    operating_room_id: Optional[int] = None
    surgery_type: Optional[str] = None
    procedure_name: Optional[str] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    status: SurgeryStatus
    urgency_level: Optional[int] = None
    participants: Optional[str] = None
    pre_op_notes: Optional[str] = None
    post_op_notes: Optional[str] = None
    complications: Optional[str] = None

    class Config:
        from_attributes = True


def _exists_or_404(db: Session, model, pk: int, name: str):
    obj = db.get(model, pk)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return obj

def _validate_fks(db: Session, patient_id: Optional[int], doctor_id: Optional[int], operating_room_id: Optional[int]):
    if patient_id is not None:
        _exists_or_404(db, patients, patient_id, "Patient")
    if doctor_id is not None:
        _exists_or_404(db, doctors, doctor_id, "Doctor")
    if operating_room_id is not None:
        _exists_or_404(db, operating_rooms, operating_room_id, "Operating room")


@router.post("/", response_model=SurgeryOut, status_code=201)
def create_surgery(payload: SurgeryCreate, db: Session = Depends(get_db)):
    _validate_fks(db, payload.patient_id, payload.doctor_id, payload.operating_room_id)
    obj = surgeries(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=List[SurgeryOut])
def list_surgeries(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    operating_room_id: Optional[int] = Query(None),
    status: Optional[SurgeryStatus] = Query(None),
    date_from: Optional[date] = Query(None, description="Filter: scheduled_date >= this date"),
    date_to: Optional[date] = Query(None, description="Filter: scheduled_date <= this date"),
    search: Optional[str] = Query(None, description="Search in procedure_name / surgery_type"),
):
    q = db.query(surgeries)
    if patient_id is not None:
        q = q.filter(surgeries.patient_id == patient_id)
    if doctor_id is not None:
        q = q.filter(surgeries.doctor_id == doctor_id)
    if operating_room_id is not None:
        q = q.filter(surgeries.operating_room_id == operating_room_id)
    if status is not None:
        q = q.filter(surgeries.status == status)
    if date_from is not None:
        q = q.filter(surgeries.scheduled_date >= date_from)
    if date_to is not None:
        q = q.filter(surgeries.scheduled_date <= date_to)
    if search:
        like = f"%{search}%"
        q = q.filter((surgeries.procedure_name.ilike(like)) | (surgeries.surgery_type.ilike(like)))
    return q.order_by(surgeries.id.desc()).offset(offset).limit(limit).all()


@router.get("/{surgery_id}", response_model=SurgeryOut)
def get_surgery(surgery_id: int, db: Session = Depends(get_db)):
    obj = db.get(surgeries, surgery_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Surgery not found")
    return obj


@router.patch("/{surgery_id}", response_model=SurgeryOut)
def update_surgery(surgery_id: int, payload: SurgeryUpdate, db: Session = Depends(get_db)):
    obj = db.get(surgeries, surgery_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Surgery not found")

    data = payload.model_dict(exclude_unset=True) if hasattr(payload, "model_dict") else payload.dict(exclude_unset=True)
    _validate_fks(db, data.get("patient_id"), data.get("doctor_id"), data.get("operating_room_id"))

    for k, v in data.items():
        setattr(obj, k, v)

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{surgery_id}", status_code=204)
def delete_surgery(surgery_id: int, db: Session = Depends(get_db)):
    obj = db.get(surgeries, surgery_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Surgery not found")
    db.delete(obj)
    db.commit()
    return None
