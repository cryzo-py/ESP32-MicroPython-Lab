import pytest
from esp32_lab.application.education.feedback.diagnosis import DiagnosisEngine
from esp32_lab.application.education.evaluation.models import EvaluationItem

def test_diagnosis_priority_filtering():
    items = [
        EvaluationItem(
            id="rule_comp", category="PHYSICAL", status="FAIL", score=0, max_score=10,
            message="Il manque le composant : led.", technical_message="", pedagogical_message=""
        ),
        EvaluationItem(
            id="rule_top", category="PHYSICAL", status="FAIL", score=0, max_score=10,
            message="Aucun chemin électrique.", technical_message="", pedagogical_message=""
        ),
        EvaluationItem(
            id="rule_code", category="CODE", status="FAIL", score=0, max_score=10,
            message="GPIO non configuré.", technical_message="", pedagogical_message=""
        )
    ]
    
    engine = DiagnosisEngine()
    diagnoses = engine.diagnose(items)
    
    # Priority 1 (COMPONENT) should filter out 4 (TOPOLOGY) and 6 (CODE)
    # Actually COMPONENT is priority 1. Wait, let's see what priority is assigned.
    assert len(diagnoses) > 0
    # The lowest priority number should be 1
    assert diagnoses[0].priority == 1
    assert "manque le composant" in diagnoses[0].cause
    
    # It should have filtered out priority 4 and 6
    for d in diagnoses:
        assert d.priority <= 2  # Highest priority found (1) + 1 max
