# app/routes/transcriptions.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, field_validator
from typing import Optional, List
from datetime import datetime

from ..dependencies import get_db
from ..models.transcription import transcriptions, TranscriptionStatus
from ..models.doctor import doctors
from ..models.patient import patients
from ..models.note import notes  # only to check uniqueness if you later want to link via notes

router = APIRouter()

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

    @field_validator("audio_duration_seconds")
    @classmethod
    def _non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("audio_duration_seconds must be >= 0")
        return v


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

    @field_validator("audio_duration_seconds")
    @classmethod
    def _non_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError("audio_duration_seconds must be >= 0")
        return v


class TranscriptionOut(BaseModel):
    id: int
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None
    audio_file_url: Optional[str] = None
    audio_duration_seconds: Optional[int] = None
    transcription_text: Optional[str] = None
    transcription_status: TranscriptionStatus
    confidence_score: Optional[float] = None
    language: Optional[str] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def _exists_or_404(db: Session, model, pk: int, name: str):
    obj = db.get(model, pk)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return obj

def _validate_fk(db: Session, doctor_id: Optional[int], patient_id: Optional[int]):
    if doctor_id is not None:
        _exists_or_404(db, doctors, doctor_id, "Doctor")
    if patient_id is not None:
        _exists_or_404(db, patients, patient_id, "Patient")

@router.post("/", response_model=TranscriptionOut, status_code=201)
def create_transcription(payload: TranscriptionCreate, db: Session = Depends(get_db)):
    _validate_fk(db, payload.doctor_id, payload.patient_id)
    obj = transcriptions(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=List[TranscriptionOut])
def list_transcriptions(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    doctor_id: Optional[int] = Query(None),
    patient_id: Optional[int] = Query(None),
    status: Optional[TranscriptionStatus] = Query(None),
    language: Optional[str] = Query(None),
    completed_from: Optional[datetime] = Query(None, description="Filter: completed_at >= this datetime"),
    completed_to: Optional[datetime] = Query(None, description="Filter: completed_at <= this datetime"),
    search: Optional[str] = Query(None, description="Search in transcription_text"),
):
    q = db.query(transcriptions)
    if doctor_id is not None:
        q = q.filter(transcriptions.doctor_id == doctor_id)
    if patient_id is not None:
        q = q.filter(transcriptions.patient_id == patient_id)
    if status is not None:
        q = q.filter(transcriptions.transcription_status == status)
    if language:
        q = q.filter(transcriptions.language == language)
    if completed_from is not None:
        q = q.filter(transcriptions.completed_at >= completed_from)
    if completed_to is not None:
        q = q.filter(transcriptions.completed_at <= completed_to)
    if search:
        like = f"%{search}%"
        q = q.filter(transcriptions.transcription_text.ilike(like))
    return q.order_by(transcriptions.id.desc()).offset(offset).limit(limit).all()


@router.get("/{transcription_id}", response_model=TranscriptionOut)
def get_transcription(transcription_id: int, db: Session = Depends(get_db)):
    obj = db.get(transcriptions, transcription_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Transcription not found")
    return obj


@router.patch("/{transcription_id}", response_model=TranscriptionOut)
def update_transcription(transcription_id: int, payload: TranscriptionUpdate, db: Session = Depends(get_db)):
    obj = db.get(transcriptions, transcription_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Transcription not found")

    data = payload.model_dict(exclude_unset=True) if hasattr(payload, "model_dict") else payload.dict(exclude_unset=True)

    # Validate any new FKs
    _validate_fk(db, data.get("doctor_id"), data.get("patient_id"))

    if data.get("transcription_status") == TranscriptionStatus.completed and not data.get("completed_at"):
        data["completed_at"] = datetime.utcnow()

    for k, v in data.items():
        setattr(obj, k, v)

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{transcription_id}", status_code=204)
def delete_transcription(transcription_id: int, db: Session = Depends(get_db)):
    obj = db.get(transcriptions, transcription_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Transcription not found")
    db.delete(obj)
    db.commit()
    return None
