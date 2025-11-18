
import whisper
import torch
from typing import Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TranscriptionService:
    
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading Whisper model '{model_size}' on {self.device}")
        
        self.model = whisper.load_model(model_size, device=self.device)
        logger.info(f"Whisper model loaded successfully")
    
    def transcribe_audio(
        self, 
        audio_path: str, 
        language: str = "en",
        task: str = "transcribe"
    ) -> Dict:
        try:
            start_time = datetime.now()
            
            # Transcribe
            result = self.model.transcribe(
                audio_path,
                language=language,
                task=task,
                fp16=False,
                verbose=False
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "text": result["text"].strip(),
                "segments": result.get("segments", []),
                "language": result.get("language", language),
                "processing_time": duration,
                "confidence": self._calculate_avg_confidence(result.get("segments", []))
            }
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": None
            }
    
    def transcribe_realtime_chunk(
        self,
        audio_path: str,
        language: str = "en",
        previous_context: Optional[str] = None
    ) -> Dict:
        result = self.transcribe_audio(audio_path, language)
        
        if result["success"] and previous_context:
            result["full_text"] = previous_context + " " + result["text"]
        
        return result
    
    def _calculate_avg_confidence(self, segments: List[Dict]) -> float:
        if not segments:
            return 0.0
        
        confidences = []
        for segment in segments:
            no_speech_prob = segment.get("no_speech_prob", 0.5)
            confidence = 1.0 - no_speech_prob
            confidences.append(confidence)
        
        return sum(confidences) / len(confidences) if confidences else 0.5

print("TranscriptionService created!")
