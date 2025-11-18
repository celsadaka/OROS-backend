
import os
import json
import logging
from typing import Dict, List, Optional
from groq import Groq
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalysisService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # Free and powerful
    
    def analyze_transcription(
        self,
        transcription_text: str,
        patient_info: Dict,
        previous_notes: List[Dict],
        context: Optional[str] = None
    ) -> Dict:
        # Build comprehensive prompt
        prompt = self._build_analysis_prompt(
            transcription_text,
            patient_info,
            previous_notes,
            context
        )
        
        try:
            start_time = datetime.now()
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower for medical accuracy
                max_tokens=2000,
                response_format={"type": "json_object"}  # Structured output
            )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            
            return {
                "success": True,
                "analysis": result.get("analysis", ""),
                "summary": result.get("summary", ""),
                "keywords": result.get("keywords", []),
                "concerns_identified": result.get("concerns", []),
                "urgency_level": result.get("urgency_level", 1),
                "processing_time": duration,
                "model_used": self.model
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_system_prompt(self) -> str:
        return """You are an expert medical AI assistant helping doctors analyze patient encounters.

Your task is to:
1. Summarize the key medical information from the doctor's notes
2. Extract important medical keywords (symptoms, diagnoses, medications, procedures)
3. Identify any concerns or risks that need attention
4. Assess urgency level (1-5, where 5 is most urgent)

Always respond in valid JSON format with these exact keys:
{
    "analysis": "detailed analysis of the medical encounter",
    "summary": "concise 2-3 sentence summary",
    "keywords": ["keyword1", "keyword2", ...],
    "concerns": ["concern1", "concern2", ...],
    "urgency_level": 1-5
}

Be thorough but concise. Focus on clinically relevant information."""
    
    def _build_analysis_prompt(
        self,
        transcription: str,
        patient_info: Dict,
        previous_notes: List[Dict],
        context: Optional[str]
    ) -> str:
        
        prompt_parts = []
        
        # Patient background
        prompt_parts.append("PATIENT INFORMATION")
        prompt_parts.append(f"Name: {patient_info.get('first_name', '')} {patient_info.get('last_name', '')}")
        if patient_info.get('date_of_birth'):
            prompt_parts.append(f"DOB: {patient_info['date_of_birth']}")
        if patient_info.get('gender'):
            prompt_parts.append(f"Gender: {patient_info['gender']}")
        if patient_info.get('allergies'):
            prompt_parts.append(f"Allergies: {patient_info['allergies']}")
        if patient_info.get('medical_history'):
            prompt_parts.append(f"Medical History: {patient_info['medical_history']}")
        
        # Previous notes context
        if previous_notes:
            prompt_parts.append("\nPREVIOUS NOTES (Most Recent)")
            for i, note in enumerate(previous_notes[:3], 1):  # Last 3 notes
                prompt_parts.append(f"\nNote {i} ({note.get('created_at', 'N/A')}):")
                prompt_parts.append(note.get('content', '')[:500])  # First 500 chars
        
        # Current transcription
        prompt_parts.append("\nCURRENT ENCOUNTER TRANSCRIPTION")
        prompt_parts.append(transcription)
        
        # Additional context
        if context:
            prompt_parts.append(f"\nADDITIONAL CONTEXT")
            prompt_parts.append(context)
        
        prompt_parts.append("\nINSTRUCTION")
        prompt_parts.append("Analyze the current encounter in context of the patient's history and previous notes. Provide structured analysis in JSON format.")
        
        return "\n".join(prompt_parts)

print("AnalysisService created!")
