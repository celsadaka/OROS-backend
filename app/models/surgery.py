from __future__ import annotations
from sqlalchemy import String, Integer, Enum, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum
from typing import Optional
from datetime import date, datetime


# Allowed statuses for a surgery record
class SurgeryStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class surgeries(Base):
    """Surgery model — connects a patient, a primary doctor, and (optionally) an operating room."""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign keys
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="RESTRICT"), index=True)
    operating_room_id: Mapped[Optional[int]] = mapped_column(ForeignKey("operating_rooms.id", ondelete="SET NULL"))

    # Descriptors
    surgery_type: Mapped[Optional[str]] = mapped_column(String(120))
    procedure_name: Mapped[Optional[str]] = mapped_column(String(200))

    # Scheduling & timing
    scheduled_date: Mapped[Optional[date]]
    scheduled_time: Mapped[Optional[str]] = mapped_column(String(10))  # per ERD
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    actual_start_time: Mapped[Optional[datetime]]
    actual_end_time: Mapped[Optional[datetime]]

    # Status / urgency
    status: Mapped[SurgeryStatus] = mapped_column(Enum(SurgeryStatus), default=SurgeryStatus.scheduled)
    urgency_level: Mapped[Optional[int]] = mapped_column(Integer)

    # Clinical text fields 
    participants: Mapped[Optional[str]] = mapped_column(String(400))  # free text list of other doctors/staff
    pre_op_notes: Mapped[Optional[str]]
    post_op_notes: Mapped[Optional[str]]
    complications: Mapped[Optional[str]]

    # Relationships
    patient = relationship("patients", back_populates="surgeries")
    doctor = relationship("doctors", back_populates="surgeries")
    operating_room = relationship("operating_rooms", back_populates="surgeries")
    notes = relationship("notes", back_populates="surgery")  # notes.surgery_id

    def __repr__(self) -> str:
        return f"<Surgery(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id}, status={self.status})>"
