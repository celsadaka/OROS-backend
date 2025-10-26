from pydantic import BaseModel
from typing import Optional
from ..models.note_analysis import AnalysisStatus
from .common import ORMBase, WithTimestamps


class NoteAnalysisBase(ORMBase):
    transcription_id: Optional[int] = None
    note_id: Optional[int] = None
    analysis: Optional[str] = None
    keywords: Optional[str] = None
    summary: Optional[str] = None
    concerns_identified: Optional[str] = None
    actions_recommended: Optional[str] = None
    urgency_level: Optional[int] = None
    analysis_status: AnalysisStatus = AnalysisStatus.pending


class NoteAnalysisCreate(BaseModel):
    transcription_id: Optional[int] = None
    note_id: Optional[int] = None
    analysis: Optional[str] = None
    keywords: Optional[str] = None
    summary: Optional[str] = None
    concerns_identified: Optional[str] = None
    actions_recommended: Optional[str] = None
    urgency_level: Optional[int] = None
    analysis_status: Optional[AnalysisStatus] = AnalysisStatus.pending


class NoteAnalysisUpdate(BaseModel):
    transcription_id: Optional[int] = None
    note_id: Optional[int] = None
    analysis: Optional[str] = None
    keywords: Optional[str] = None
    summary: Optional[str] = None
    concerns_identified: Optional[str] = None
    actions_recommended: Optional[str] = None
    urgency_level: Optional[int] = None
    analysis_status: Optional[AnalysisStatus] = None


class NoteAnalysisOut(NoteAnalysisBase, WithTimestamps):
    id: int

    class Config:
        from_attributes = True
