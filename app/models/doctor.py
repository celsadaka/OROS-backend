from __future__ import annotations
from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum
from typing import Optional


# Define allowed doctor statuses
class DoctorStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class doctors(Base):
    """Doctor model — represents a hospital doctor or staff member."""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(40))
    specialization: Mapped[Optional[str]] = mapped_column(String(120))
    license_number: Mapped[Optional[str]] = mapped_column(String(120))
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(512))
    status: Mapped[DoctorStatus] = mapped_column(Enum(DoctorStatus), default=DoctorStatus.active)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    notes = relationship("notes", back_populates="doctor")
    surgeries = relationship("surgeries", back_populates="doctor")
    transcriptions = relationship("transcriptions", back_populates="doctor")
    notifications = relationship("notifications", back_populates="doctor")

    def __repr__(self) -> str:
        return f"<Doctor(id={self.id}, name={self.first_name} {self.last_name})>"
