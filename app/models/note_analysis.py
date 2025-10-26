from __future__ import annotations
from sqlalchemy import String, Integer, Enum, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
import enum
from typing import Optional


class AnalysisStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"


class note_analysis(Base):
    """AI analysis results for a note (optionally tied to a transcription)."""

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Optional links (either/both may be present)
    transcription_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("transcriptions.id", ondelete="SET NULL"), index=True
    )
    note_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("notes.id", ondelete="CASCADE"), index=True
    )

    # Analysis content
    analysis: Mapped[Optional[str]] = mapped_column(Text)              # full analysis blob (JSON or text)
    keywords: Mapped[Optional[str]] = mapped_column(Text)              # comma-separated or JSON array
    summary: Mapped[Optional[str]] = mapped_column(Text)
    concerns_identified: Mapped[Optional[str]] = mapped_column(Text)   # risks/flags
    actions_recommended: Mapped[Optional[str]] = mapped_column(Text)   # follow-ups / tasks
    urgency_level: Mapped[Optional[int]] = mapped_column(Integer)      # 1–5 or similar scale
    analysis_status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus), default=AnalysisStatus.pending
    )

    # Relationships
    note = relationship("notes", back_populates="analyses")

    __table_args__ = (
        Index("ix_note_analysis_note_created", "note_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<NoteAnalysis(id={self.id}, status={self.analysis_status})>"
