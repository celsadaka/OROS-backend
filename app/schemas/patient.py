from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date
from ..models.patient import PatientStatus
from .common import ORMBase, WithTimestamps

class PatientBase(ORMBase):
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
    date_of_birth: Optional[date] = None
    status: PatientStatus = PatientStatus.active

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
    date_of_birth: Optional[date] = None


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
    date_of_birth: Optional[date] = None
    status: Optional[PatientStatus] = None

class PatientOut(PatientBase, WithTimestamps):
    id: int

    class Config:
        from_attributes = True
