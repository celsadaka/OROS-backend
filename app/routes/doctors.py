# app/routes/doctors.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from ..dependencies import get_db
from ..auth import hash_password
from ..models.doctor import doctors, DoctorStatus

router = APIRouter()


# -------------------- Schemas --------------------
class DoctorCreate(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    profile_image_url: Optional[str] = None


class DoctorUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    status: Optional[DoctorStatus] = None


class DoctorOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    status: DoctorStatus

    class Config:
        from_attributes = True


# -------------------- Helpers --------------------
def _ensure_unique_email(db: Session, email: str, exclude_id: Optional[int] = None):
    q = db.query(doctors).filter(doctors.email == email)
    if exclude_id is not None:
        q = q.filter(doctors.id != exclude_id)
    exists = db.query(q.exists()).scalar()
    if exists:
        raise HTTPException(status_code=400, detail="Email already exists")


# -------------------- Endpoints --------------------
@router.post("/", response_model=DoctorOut, status_code=201)
def create_doctor(payload: DoctorCreate, db: Session = Depends(get_db)):
    _ensure_unique_email(db, payload.email)
    obj = doctors(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        password_hash=hash_password(payload.password),  # store hash, not plain text
        phone=payload.phone,
        specialization=payload.specialization,
        license_number=payload.license_number,
        profile_image_url=payload.profile_image_url,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=List[DoctorOut])
def list_doctors(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None, description="Search by first/last name or email"),
):
    q = db.query(doctors)
    if search:
        like = f"%{search}%"
        q = q.filter(
            (doctors.first_name.ilike(like)) |
            (doctors.last_name.ilike(like)) |
            (doctors.email.ilike(like))
        )
    return q.order_by(doctors.id.desc()).offset(offset).limit(limit).all()


@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: int, db: Session = Depends(get_db)):
    obj = db.get(doctors, doctor_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return obj


@router.patch("/{doctor_id}", response_model=DoctorOut)
def update_doctor(doctor_id: int, payload: DoctorUpdate, db: Session = Depends(get_db)):
    obj = db.get(doctors, doctor_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Doctor not found")

    data = payload.model_dict(exclude_unset=True) if hasattr(payload, "model_dict") else payload.dict(exclude_unset=True)

    if "email" in data and data["email"] is not None:
        _ensure_unique_email(db, data["email"], exclude_id=doctor_id)

    if "password" in data and data["password"]:
        obj.password_hash = hash_password(data.pop("password"))

    for k, v in data.items():
        setattr(obj, k, v)

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{doctor_id}", status_code=204)
def delete_doctor(doctor_id: int, db: Session = Depends(get_db)):
    obj = db.get(doctors, doctor_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Doctor not found")
    db.delete(obj)
    db.commit()
    return None
