from __future__ import annotations
from sqlalchemy import String, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from typing import Optional


class notes(Base):
    """Clinical note — the reviewed/edited record (may be linked to a transcription and/or a surgery)."""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Foreign keys
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id", ondelete="RESTRICT"), index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="RESTRICT"), index=True)
    surgery_id: Mapped[Optional[int]] = mapped_column(ForeignKey("surgeries.id", ondelete="SET NULL"))

    # Optional 1:1 link to a transcription (no back FK in transcriptions to avoid cycles)
    transcription_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transcriptions.id", ondelete="SET NULL"),
        unique=True,  # enforce 1:1 when present
        nullable=True
    )

    # Content
    title: Mapped[Optional[str]] = mapped_column(String(200))
    content: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    patient = relationship("patients", back_populates="notes")
    doctor = relationship("doctors", back_populates="notes")
    surgery = relationship("surgeries", back_populates="notes")
    transcription = relationship("transcriptions", back_populates="note")
    analyses = relationship("note_analysis", back_populates="note", cascade="all, delete-orphan")

    # Helpful composite index for common queries
    __table_args__ = (
        Index("ix_notes_doctor_created", "doctor_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Note(id={self.id}, patient_id={self.patient_id}, doctor_id={self.doctor_id})>"
