from typing import List, Dict, Any
from .models import ErrorDiagnosis
from esp32_lab.application.education.evaluation.models import EvaluationItem

class DiagnosisEngine:
    """Translates EvaluationItems into prioritized ErrorDiagnosis to prevent cascading errors."""
    
    CATEGORY_PRIORITY = {
        "COMPONENT": 1,
        "PLACEMENT": 2,
        "PHYSICAL": 3,
        "TOPOLOGY": 4,
        "CONFIGURATION": 5,
        "CODE": 6,
        "BEHAVIOR": 7,
        "LEGACY": 8
    }

    def diagnose(self, evaluation_items: List[EvaluationItem]) -> List[ErrorDiagnosis]:
        diagnoses = []
        
        for item in evaluation_items:
            if item.status == "FAIL":
                cat = item.category
                priority = self.CATEGORY_PRIORITY.get(cat, 99)
                # Specific logic: if it's missing component in PHYSICAL, we assign COMPONENT priority
                if "manque" in item.message.lower() or "manquant" in item.message.lower():
                    priority = self.CATEGORY_PRIORITY["COMPONENT"]
                    
                diagnoses.append(ErrorDiagnosis(
                    category=cat,
                    cause=item.message,
                    evidence=item.technical_message,
                    priority=priority,
                    rule_id=item.id
                ))
                
        # Filter cascading errors.
        # If there are priority 1 errors, do not show priority 4 (topology) or 6 (code) if they depend on it.
        # For simplicity, if we have a missing component (priority 1), we filter out topology errors (priority 4).
        
        filtered = []
        highest_priority_found = min([d.priority for d in diagnoses], default=99)
        
        for d in diagnoses:
            # Simple heuristic: only show errors that are in the highest active priority bucket
            # + 1 level max, to avoid overwhelming the student.
            if d.priority <= highest_priority_found + 1:
                filtered.append(d)
                
        return sorted(filtered, key=lambda x: x.priority)
