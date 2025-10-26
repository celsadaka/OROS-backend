# app/routes/patients.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Set

from ..dependencies import get_db
from ..auth import get_current_doctor
from ..models.doctor import doctors
from ..models.patient import patients, PatientStatus
from ..models.surgery import surgeries
from ..models.note import notes
from ..models.transcription import transcriptions

router = APIRouter()


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    insurance_info: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    address: Optional[str] = None
    profile_image_url: Optional[str] = None


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    gender: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None
    medical_history: Optional[str] = None
    insurance_info: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    address: Optional[str] = None
    profile_image_url: Optional[str] = None
    status: Optional[PatientStatus] = None


class PatientOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: PatientStatus

    class Config:
        from_attributes = True


@router.post("/", response_model=PatientOut, status_code=201)
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    obj = patients(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=List[PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search by first/last name, email, or phone"),
):
    q = db.query(patients)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (patients.first_name.ilike(like)) |
            (patients.last_name.ilike(like)) |
            (patients.email.ilike(like)) |
            (patients.phone.ilike(like))
        )
    return q.order_by(patients.id.desc()).offset(offset).limit(limit).all()


@router.get("/my", response_model=List[PatientOut], summary="List patients associated to the current doctor")
def list_my_patients(
    current_doctor: doctors = Depends(get_current_doctor),
    db: Session = Depends(get_db),
):
    """
    Return a distinct set of patients that have been linked to the authenticated doctor
    through surgeries, notes, or transcriptions.
    """
    patient_ids: Set[int] = set()

    patient_ids.update(
        pid for (pid,) in (
            db.query(patients.id)
            .join(surgeries, surgeries.patient_id == patients.id)
            .filter(surgeries.doctor_id == current_doctor.id)
            .all()
        )
    )
    patient_ids.update(
        pid for (pid,) in (
            db.query(patients.id)
            .join(notes, notes.patient_id == patients.id)
            .filter(notes.doctor_id == current_doctor.id)
            .all()
        )
    )
    patient_ids.update(
        pid for (pid,) in (
            db.query(patients.id)
            .join(transcriptions, transcriptions.patient_id == patients.id)
            .filter(transcriptions.doctor_id == current_doctor.id)
            .all()
        )
    )

    if not patient_ids:
        return []

    return (
        db.query(patients)
        .filter(patients.id.in_(patient_ids))
        .order_by(patients.last_name.asc(), patients.first_name.asc(), patients.id.asc())
        .all()
    )


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    obj = db.get(patients, patient_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Patient not found")
    return obj


@router.patch("/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, payload: PatientUpdate, db: Session = Depends(get_db)):
    obj = db.get(patients, patient_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Patient not found")

    data = payload.model_dict(exclude_unset=True) if hasattr(payload, "model_dict") else payload.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{patient_id}", status_code=204)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    obj = db.get(patients, patient_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(obj)
    db.commit()
    return None
