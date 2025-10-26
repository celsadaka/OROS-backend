from __future__ import annotations
from sqlalchemy import String, Integer, Boolean, Enum, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum
from typing import Optional
from datetime import datetime


# Define priority levels
class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class notifications(Base):
    """Notification model — alerts sent to doctors about system events (linked to any entity)."""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    priority: Mapped[Priority] = mapped_column(Enum(Priority), default=Priority.low)

    # Whether the notification has been read
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    # Generic link to any entity (note, surgery, transcription, etc.)
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(50))
    related_entity_id: Mapped[Optional[int]]

    # Who receives the notification
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), index=True)
    doctor = relationship("doctors", back_populates="notifications")

    # When it was read
    read_at: Mapped[Optional[datetime]]

    # Index for quick lookups
    __table_args__ = (
        Index("ix_notifications_doctor_created", "doctor_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, doctor_id={self.doctor_id}, title={self.title})>"
