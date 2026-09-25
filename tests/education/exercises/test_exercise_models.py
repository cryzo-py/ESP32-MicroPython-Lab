import pytest
from esp32_lab.application.education.exercises.models import Exercise, ExerciseMission
from esp32_lab.application.education.exercises.validator import ExerciseValidator
from esp32_lab.application.education.exercises.loader import ExerciseLoader

def test_exercise_validator_valid():
    data = {
        "id": "ex_1",
        "title": "Title",
        "mission": {
            "context": "Context",
            "mission": "Mission",
            "objective": "Objective"
        },
        "evaluation_rules": []
    }
    is_valid, errors = ExerciseValidator.validate(data)
    assert is_valid is True
    assert len(errors) == 0

def test_exercise_validator_invalid():
    data = {
        "id": "ex_1",
        # Missing title and evaluation_rules
        "mission": {
            "context": "Context" # Missing mission and objective
        }
    }
    is_valid, errors = ExerciseValidator.validate(data)
    assert is_valid is False
    assert len(errors) > 0
    assert any("title" in e for e in errors)
    assert any("objective" in e for e in errors)

def test_exercise_loader():
    data = {
        "id": "ex_1",
        "title": "Title",
        "mission": {
            "context": "C",
            "mission": "M",
            "objective": "O"
        },
        "evaluation_rules": [{"id": "r1"}],
        "skills": ["GPIO"]
    }
    ex = ExerciseLoader.load_from_dict(data)
    assert ex.id == "ex_1"
    assert ex.mission.context == "C"
    assert "GPIO" in ex.skills
    assert len(ex.evaluation_rules) == 1
