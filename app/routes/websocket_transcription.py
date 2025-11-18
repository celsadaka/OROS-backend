
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
import json
import logging
import base64
from datetime import datetime

from ..dependencies import get_db
from ..models.transcription import transcriptions, TranscriptionStatus
from ..models.patient import patients
from ..services.audio_processor import AudioProcessor
from ..services.transcription_service import TranscriptionService
from ..services.analysis_service import AnalysisService
from ..services.medical_ner import MedicalNER

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services (singleton)
audio_processor = AudioProcessor()
transcription_service = TranscriptionService(model_size="base")
analysis_service = AnalysisService()
medical_ner = MedicalNER()


class ConnectionManager:
    
    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}
    
    async def connect(self, transcription_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[transcription_id] = websocket
        logger.info(f"WebSocket connected for transcription {transcription_id}")
    
    def disconnect(self, transcription_id: int):
        if transcription_id in self.active_connections:
            del self.active_connections[transcription_id]
            logger.info(f"WebSocket disconnected for transcription {transcription_id}")
    
    async def send_message(self, transcription_id: int, message: dict):
        if transcription_id in self.active_connections:
            websocket = self.active_connections[transcription_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message: {str(e)}")
                self.disconnect(transcription_id)


manager = ConnectionManager()


@router.websocket("/ws/transcribe/{transcription_id}")
async def websocket_transcribe(
    websocket: WebSocket,
    transcription_id: int,
    db: Session = Depends(get_db)
):
    
    await manager.connect(transcription_id, websocket)
    
    # Get transcription record
    transcription_record = db.get(transcriptions, transcription_id)
    if not transcription_record:
        await websocket.send_json({
            "type": "error",
            "message": "Transcription not found"
        })
        await websocket.close()
        return
    
    # Update status
    transcription_record.transcription_status = TranscriptionStatus.in_progress
    db.commit()
    
    accumulated_text = ""
    chunk_paths = []
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "audio_chunk":
                # Process audio chunk
                chunk_data = data.get("data")  # Base64 encoded audio
                chunk_index = data.get("chunk_index", 0)
                is_final = data.get("is_final", False)
                
                # Decode audio
                audio_bytes = base64.b64decode(chunk_data)
                
                # Save chunk
                chunk_path = audio_processor.save_audio_chunk(
                    audio_bytes,
                    transcription_id,
                    chunk_index
                )
                chunk_paths.append(chunk_path)
                
                # Convert to WAV
                wav_path = audio_processor.convert_to_wav(chunk_path)
                
                # Transcribe chunk
                result = transcription_service.transcribe_realtime_chunk(
                    wav_path,
                    language=transcription_record.language or "en",
                    previous_context=accumulated_text
                )
                
                if result["success"]:
                    chunk_text = result["text"]
                    accumulated_text += " " + chunk_text
                    
                    # Extract entities
                    entities = medical_ner.extract_entities(chunk_text)
                    
                    # Send update to client
                    await manager.send_message(transcription_id, {
                        "type": "transcription_update",
                        "text": chunk_text,
                        "full_text": accumulated_text.strip(),
                        "is_partial": not is_final,
                        "chunk_index": chunk_index,
                        "entities": entities,
                        "confidence": result.get("confidence", 0.0)
                    })
                    
                    # Update database
                    transcription_record.transcription_text = accumulated_text.strip()
                    transcription_record.confidence_score = result.get("confidence")
                    db.commit()
                
                # If final chunk, process complete transcription
                if is_final:
                    await process_final_transcription(
                        transcription_record,
                        accumulated_text.strip(),
                        chunk_paths,
                        db,
                        transcription_id
                    )
                    break
            
            elif message_type == "cancel":
                # User cancelled recording
                transcription_record.transcription_status = TranscriptionStatus.failed
                db.commit()
                break
    
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from transcription {transcription_id}")
        manager.disconnect(transcription_id)
    
    except Exception as e:
        logger.error(f"Error in WebSocket: {str(e)}")
        await manager.send_message(transcription_id, {
            "type": "error",
            "message": str(e)
        })
        transcription_record.transcription_status = TranscriptionStatus.failed
        db.commit()
    
    finally:
        # Cleanup
        audio_processor.cleanup_chunks(chunk_paths)
        manager.disconnect(transcription_id)


async def process_final_transcription(
    transcription_record: transcriptions,
    full_text: str,
    chunk_paths: list,
    db: Session,
    transcription_id: int
):
    
    # Send status
    await manager.send_message(transcription_id, {
        "type": "status",
        "message": "Analyzing..."
    })
    
    # Get patient and previous notes context
    patient = None
    previous_notes = []
    
    if transcription_record.patient_id:
        patient = db.get(patients, transcription_record.patient_id)
        
        # Get previous notes
        from ..models.note import notes
        previous_notes = (
            db.query(notes)
            .filter(notes.patient_id == transcription_record.patient_id)
            .order_by(notes.created_at.desc())
            .limit(5)
            .all()
        )
    
    # Prepare patient info
    patient_info = {}
    if patient:
        patient_info = {
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
            "gender": patient.gender,
            "allergies": patient.allergies,
            "medical_history": patient.medical_history
        }
    
    previous_notes_data = [
        {
            "created_at": str(note.created_at),
            "content": note.content,
            "title": note.title
        }
        for note in previous_notes
    ]
    
    # Run analysis
    analysis_result = analysis_service.analyze_transcription(
        full_text,
        patient_info,
        previous_notes_data,
        context=None
    )
    
    # Extract all entities
    all_entities = medical_ner.extract_entities(full_text)
    
    if analysis_result["success"]:
        # Store analysis
        from ..models.note_analysis import note_analysis, AnalysisStatus
        
        analysis_record = note_analysis(
            transcription_id=transcription_id,
            analysis=analysis_result.get("analysis"),
            keywords=",".join(analysis_result.get("keywords", [])),
            summary=analysis_result.get("summary"),
            concerns_identified=json.dumps(analysis_result.get("concerns_identified", [])),
            urgency_level=analysis_result.get("urgency_level", 1),
            analysis_status=AnalysisStatus.completed
        )
        
        db.add(analysis_record)
        
        # Send analysis to client
        await manager.send_message(transcription_id, {
            "type": "analysis_complete",
            "analysis": analysis_result,
            "entities": all_entities
        })
    
    # Update transcription status
    transcription_record.transcription_status = TranscriptionStatus.completed
    transcription_record.completed_at = datetime.utcnow()
    
    db.commit()
    
    # Send completion message
    await manager.send_message(transcription_id, {
        "type": "complete",
        "message": "Transcription and analysis complete",
        "transcription_id": transcription_id
    })

