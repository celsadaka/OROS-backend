from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..models.transcription import TranscriptionStatus
from .common import ORMBase, WithTimestamps

class TranscriptionBase(ORMBase):
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None
    audio_file_url: Optional[str] = None
    audio_duration_seconds: Optional[int] = None
    transcription_text: Optional[str] = None
    transcription_status: TranscriptionStatus = TranscriptionStatus.pending
    confidence_score: Optional[float] = None
    language: Optional[str] = None
    completed_at: Optional[datetime] = None


class TranscriptionCreate(BaseModel):
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None
    audio_file_url: Optional[str] = None
    audio_duration_seconds: Optional[int] = None
    transcription_text: Optional[str] = None
    transcription_status: Optional[TranscriptionStatus] = TranscriptionStatus.pending
    confidence_score: Optional[float] = None
    language: Optional[str] = None
    completed_at: Optional[datetime] = None


class TranscriptionUpdate(BaseModel):
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None
    audio_file_url: Optional[str] = None
    audio_duration_seconds: Optional[int] = None
    transcription_text: Optional[str] = None
    transcription_status: Optional[TranscriptionStatus] = None
    confidence_score: Optional[float] = None
    language: Optional[str] = None
    completed_at: Optional[datetime] = None


# -------------------- Response --------------------
class TranscriptionOut(TranscriptionBase, WithTimestamps):
    id: int

    class Config:
        from_attributes = True
