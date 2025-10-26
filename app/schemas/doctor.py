from pydantic import BaseModel, EmailStr
from typing import Optional
from ..models.doctor import DoctorStatus
from .common import ORMBase, WithTimestamps


class DoctorBase(ORMBase):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    specialization: Optional[str] = None
    license_number: Optional[str] = None
    profile_image_url: Optional[str] = None
    status: DoctorStatus = DoctorStatus.active


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


class DoctorOut(DoctorBase, WithTimestamps):
    id: int

    class Config:
        from_attributes = True
