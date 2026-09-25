import pytest
import html
from esp32_lab.application.education.feedback.feedback_engine import FeedbackEngine
from esp32_lab.application.education.evaluation.models import EvaluationItem
from esp32_lab.application.education.feedback.models import ErrorDiagnosis

def test_feedback_engine_security():
    engine = FeedbackEngine()
    
    # Simulate an adversarial diagnosis with XSS
    diag = ErrorDiagnosis(
        category="CODE",
        cause="Code failure <script>alert(1)</script>",
        evidence="Some evidence & things",
        priority=1,
        rule_id="rule1"
    )
    
    feedbacks = engine.generate_feedbacks([diag], [], {})
    
    assert len(feedbacks) == 1
    assert "<script>" not in feedbacks[0].message
    assert "&lt;script&gt;" in feedbacks[0].message
