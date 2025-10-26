# app/routes/notes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from ..dependencies import get_db
from ..models.note import notes
from ..models.patient import patients
from ..models.doctor import doctors
from ..models.surgery import surgeries
from ..models.transcription import transcriptions

router = APIRouter()

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


class NoteOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    surgery_id: Optional[int] = None
    transcription_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None

    class Config:
        from_attributes = True


def _exists_or_404(db: Session, model, pk: int, name: str):
    obj = db.get(model, pk)
    if not obj:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return obj

def _validate_fk_links(
    db: Session,
    patient_id: Optional[int] = None,
    doctor_id: Optional[int] = None,
    surgery_id: Optional[int] = None,
    transcription_id: Optional[int] = None,
    current_note_id: Optional[int] = None,
):
    if patient_id is not None:
        _exists_or_404(db, patients, patient_id, "Patient")
    if doctor_id is not None:
        _exists_or_404(db, doctors, doctor_id, "Doctor")
    if surgery_id is not None:
        _exists_or_404(db, surgeries, surgery_id, "Surgery")
    if transcription_id is not None:
        _exists_or_404(db, transcriptions, transcription_id, "Transcription")
        # Enforce 1:1: the same transcription cannot be linked to multiple notes
        q = db.query(notes).filter(notes.transcription_id == transcription_id)
        if current_note_id is not None:
            q = q.filter(notes.id != current_note_id)
        if db.query(q.exists()).scalar():
            raise HTTPException(status_code=400, detail="This transcription is already linked to another note")


@router.post("/", response_model=NoteOut, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    # Validate foreign keys and unique transcription link
    _validate_fk_links(
        db,
        patient_id=payload.patient_id,
        doctor_id=payload.doctor_id,
        surgery_id=payload.surgery_id,
        transcription_id=payload.transcription_id,
    )
    obj = notes(**payload.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/", response_model=List[NoteOut])
def list_notes(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    patient_id: Optional[int] = Query(None),
    doctor_id: Optional[int] = Query(None),
    surgery_id: Optional[int] = Query(None),
    has_transcription: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search in title/content"),
):
    q = db.query(notes)
    if patient_id is not None:
        q = q.filter(notes.patient_id == patient_id)
    if doctor_id is not None:
        q = q.filter(notes.doctor_id == doctor_id)
    if surgery_id is not None:
        q = q.filter(notes.surgery_id == surgery_id)
    if has_transcription is True:
        q = q.filter(notes.transcription_id.isnot(None))
    elif has_transcription is False:
        q = q.filter(notes.transcription_id.is_(None))
    if search:
        like = f"%{search}%"
        q = q.filter((notes.title.ilike(like)) | (notes.content.ilike(like)))
    return q.order_by(notes.id.desc()).offset(offset).limit(limit).all()


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db)):
    obj = db.get(notes, note_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Note not found")
    return obj


@router.patch("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)):
    obj = db.get(notes, note_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Note not found")

    data = payload.model_dict(exclude_unset=True) if hasattr(payload, "model_dict") else payload.dict(exclude_unset=True)

    # Validate any FKs included in the patch; also enforce unique transcription binding
    _validate_fk_links(
        db,
        patient_id=data.get("patient_id"),
        doctor_id=data.get("doctor_id"),
        surgery_id=data.get("surgery_id"),
        transcription_id=data.get("transcription_id"),
        current_note_id=note_id,
    )

    for k, v in data.items():
        setattr(obj, k, v)

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    obj = db.get(notes, note_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(obj)
    db.commit()
    return None
