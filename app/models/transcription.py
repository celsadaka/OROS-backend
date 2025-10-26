from _future_ import annotations
from sqlalchemy import String, Integer, Float, Enum, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum
from typing import Optional
from datetime import datetime


# Transcription pipeline status
class TranscriptionStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class transcriptions(Base):
    """Raw audio-to-text artifacts created from doctor recordings."""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Optional FKs so a transcription can exist before a Note is created
    doctor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("doctors.id", ondelete="SET NULL"), index=True)
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id", ondelete="SET NULL"), index=True)

    # Audio + ASR data
    audio_file_url: Mapped[Optional[str]] = mapped_column(String(512))
    audio_duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    transcription_text: Mapped[Optional[str]] = mapped_column(Text)
    transcription_status: Mapped[TranscriptionStatus] = mapped_column(
        Enum(TranscriptionStatus), default=TranscriptionStatus.pending
    )
    confidence_score: Mapped[Optional[float]] = mapped_column(Float)
    language: Mapped[Optional[str]] = mapped_column(String(16))
    completed_at: Mapped[Optional[datetime]]

    # Relationships
    doctor = relationship("doctors", back_populates="transcriptions")
    patient = relationship("patients", back_populates="transcriptions")
    note = relationship("notes", back_populates="transcription", uselist=False)  # notes.transcription_id (unique)

    _table_args_ = (
        Index("ix_transcriptions_doctor_created", "doctor_id", "created_at"),
    )

    def _repr_(self) -> str:
        return f"<Transcription(id={self.id}, status={self.transcription_status})>"
