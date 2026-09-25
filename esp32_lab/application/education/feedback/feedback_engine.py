from typing import List, Dict, Any
from .models import FeedbackMessage, ErrorDiagnosis
from esp32_lab.application.education.evaluation.models import EvaluationItem
from .hint_engine import HintEngine
import html

class FeedbackEngine:
    def __init__(self, hint_engine: HintEngine = None):
        self.hint_engine = hint_engine or HintEngine()

    def generate_feedbacks(self, diagnoses: List[ErrorDiagnosis], successes: List[EvaluationItem], rules_metadata: Dict[str, Any]) -> List[FeedbackMessage]:
        feedbacks = []
        
        # Add success feedbacks (limit to keep it pedagogical and not overwhelming)
        for suc in successes:
            feedbacks.append(FeedbackMessage(
                id=f"suc_{suc.id}",
                category=suc.category,
                severity="SUCCESS",
                title="Validation réussie",
                message=html.escape(suc.message),
                technical_explanation="",
                pedagogical_explanation=html.escape(suc.pedagogical_message),
                related_rule=suc.id
            ))
            
        # Add error feedbacks
        for diag in diagnoses:
            rule_meta = rules_metadata.get(diag.rule_id, {})
            rule_type = rule_meta.get("type", "unknown")
            
            hints = self.hint_engine.get_hints_for_rule(rule_type, rule_meta)
            
            feedbacks.append(FeedbackMessage(
                id=f"err_{diag.rule_id}",
                category=diag.category,
                severity="ERROR",
                title="Erreur identifiée",
                message=html.escape(diag.cause),
                technical_explanation=html.escape(diag.evidence),
                pedagogical_explanation="Une erreur bloque la réussite de l'exercice.",
                related_rule=diag.rule_id,
                hints_text=hints,
                hints_available=len(hints)
            ))
            
        return feedbacks
