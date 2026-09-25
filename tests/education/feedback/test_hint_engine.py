import pytest
from esp32_lab.application.education.feedback.hint_engine import HintEngine

def test_hint_engine_basic():
    engine = HintEngine(lang="fr")
    # Even if fr.json is minimal, we check the fallback or loaded data
    hints = engine.get_hints_for_rule("topology", {"source": "GPIO2", "dest": "LED"})
    assert isinstance(hints, list)
    
def test_hint_penalty():
    engine = HintEngine()
    engine.hint_cost_policy = 5
    assert engine.calculate_hint_penalty(3) == 15
