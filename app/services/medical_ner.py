
from typing import List, Dict
import re
import spacy
from spacy.matcher import PhraseMatcher
import logging

logger = logging.getLogger(__name__)

class MedicalNER:
    def __init__(self):
      
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy model")
        except:
            logger.warning("spaCy model not available")
            self.nlp = None
        
        # Initialize matchers for medical terms
        if self.nlp:
            self.symptom_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            self.medication_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            self.procedure_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
            
            # Load medical vocabularies
            self._load_medical_vocabularies()
    
    def _load_medical_vocabularies(self):
        
        # Common symptoms
        symptoms = [
            "fever", "pain", "headache", "nausea", "vomiting", "dizziness",
            "fatigue", "weakness", "shortness of breath", "chest pain",
            "abdominal pain", "back pain", "cough", "sore throat",
            "diarrhea", "constipation", "rash", "swelling", "bleeding"
        ]
        
        # Common medications
        medications = [
            "aspirin", "ibuprofen", "acetaminophen", "paracetamol",
            "amoxicillin", "penicillin", "metformin", "insulin",
            "lisinopril", "atorvastatin", "omeprazole", "warfarin"
        ]
        
        # Common procedures
        procedures = [
            "x-ray", "CT scan", "MRI", "ultrasound", "blood test",
            "biopsy", "surgery", "ECG", "EKG", "echocardiogram"
        ]
        
        # Add patterns to matchers
        symptom_patterns = [self.nlp.make_doc(text) for text in symptoms]
        medication_patterns = [self.nlp.make_doc(text) for text in medications]
        procedure_patterns = [self.nlp.make_doc(text) for text in procedures]
        
        self.symptom_matcher.add("SYMPTOM", symptom_patterns)
        self.medication_matcher.add("MEDICATION", medication_patterns)
        self.procedure_matcher.add("PROCEDURE", procedure_patterns)
    
    def extract_entities(self, text: str) -> Dict[str, List[Dict]]:
        if not self.nlp:
            return {}
        
        doc = self.nlp(text)
        
        entities = {
            "symptoms": [],
            "medications": [],
            "procedures": [],
            "lab_values": []
        }
        
        # Use phrase matchers for specific medical terms
        symptom_matches = self.symptom_matcher(doc)
        for match_id, start, end in symptom_matches:
            entities["symptoms"].append({
                "text": doc[start:end].text,
                "start": doc[start].idx,
                "end": doc[end-1].idx + len(doc[end-1])
            })
        
        medication_matches = self.medication_matcher(doc)
        for match_id, start, end in medication_matches:
            entities["medications"].append({
                "text": doc[start:end].text,
                "start": doc[start].idx,
                "end": doc[end-1].idx + len(doc[end-1])
            })
        
        procedure_matches = self.procedure_matcher(doc)
        for match_id, start, end in procedure_matches:
            entities["procedures"].append({
                "text": doc[start:end].text,
                "start": doc[start].idx,
                "end": doc[end-1].idx + len(doc[end-1])
            })
        
        # Extract lab values (pattern matching)
        lab_values = self._extract_lab_values(text)
        entities["lab_values"] = lab_values
        
        # Remove duplicates
        for category in entities:
            entities[category] = self._deduplicate_entities(entities[category])
        
        return entities
    
    def _extract_lab_values(self, text: str) -> List[Dict]:
        lab_values = []
        
        # Pattern for lab values: number + unit
        patterns = [
            r'\d+/\d+\s*mmHg',  # Blood pressure
            r'\d+\.?\d*\s*°?[FC]',  # Temperature
            r'\d+\.?\d*\s*(?:mg/dL|mmol/L|g/dL|%|bpm|kg|lbs)',  # Various units
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                lab_values.append({
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return lab_values
    
    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        
        for entity in entities:
            key = (entity["text"].lower(), entity.get("start", 0))
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        
        return unique
    
    def get_entity_summary(self, text: str) -> Dict[str, int]:
        entities = self.extract_entities(text)
        
        return {
            category: len(entity_list)
            for category, entity_list in entities.items()
            if entity_list
        }

print("MedicalNER created!")
