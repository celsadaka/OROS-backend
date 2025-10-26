from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from ..models.surgery import SurgeryStatus
from .common import ORMBase, WithTimestamps

class SurgeryBase(ORMBase):
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

    status: SurgeryStatus = SurgeryStatus.scheduled
    urgency_level: Optional[int] = None

    participants: Optional[str] = None
    pre_op_notes: Optional[str] = None
    post_op_notes: Optional[str] = None
    complications: Optional[str] = None


class SurgeryCreate(BaseModel):
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


class SurgeryOut(SurgeryBase, WithTimestamps):
    id: int

    class Config:
        from_attributes = True
