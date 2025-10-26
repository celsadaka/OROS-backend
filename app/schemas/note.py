from pydantic import BaseModel
from typing import Optional
from ..models.note import notes
from .common import ORMBase, WithTimestamps


class NoteBase(ORMBase):
    patient_id: int
    doctor_id: int
    surgery_id: Optional[int] = None
    transcription_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None


class NoteCreate(BaseModel):
    patient_id: int
    doctor_id: int
    surgery_id: Optional[int] = None
    transcription_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None


class NoteUpdate(BaseModel):
    patient_id: Optional[int] = None
    doctor_id: Optional[int] = None
    surgery_id: Optional[int] = None
    transcription_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None


class NoteOut(NoteBase, WithTimestamps):
    id: int

    class Config:
        from_attributes = True
