from __future__ import annotations
from sqlalchemy import String, Enum, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum
from typing import Optional
from datetime import date


# Define allowed patient statuses
class PatientStatus(str, enum.Enum):
    active = "active"
    archived = "archived"


class patients(Base):
    """Patient model — stores patient personal and medical details."""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    date_of_birth: Mapped[Optional[date]]
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(40))
    address: Mapped[Optional[str]] = mapped_column(String(255))
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(120))
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(40))
    blood_type: Mapped[Optional[str]] = mapped_column(String(8))
    allergies: Mapped[Optional[str]] = mapped_column(String(255))
    medical_history: Mapped[Optional[str]] = mapped_column(String(512))
    insurance_info: Mapped[Optional[str]] = mapped_column(String(255))
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(512))
    status: Mapped[PatientStatus] = mapped_column(Enum(PatientStatus), default=PatientStatus.active)

    # Relationships
    notes = relationship("notes", back_populates="patient")
    surgeries = relationship("surgeries", back_populates="patient")
    transcriptions = relationship("transcriptions", back_populates="patient")

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, name={self.first_name} {self.last_name})>"
