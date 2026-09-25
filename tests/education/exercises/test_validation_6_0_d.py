import pytest
import json
import random
from esp32_lab.application.education.exercises.models import Exercise, ExerciseMission, ExerciseState
from esp32_lab.application.education.exercises.validator import ExerciseValidator
from esp32_lab.application.education.exercises.loader import ExerciseLoader
from esp32_lab.application.education.exercises.engine import ExerciseEngine
from esp32_lab.application.education.evaluation.engine import EvaluationEngine
from esp32_lab.application.education.feedback.feedback_engine import FeedbackEngine
from esp32_lab.application.education.feedback.diagnosis import DiagnosisEngine
from esp32_lab.application.education.feedback.progression import ProgressionEngine, AttemptRepository, ProgressRepository
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.models.component import ComponentModel

def test_validator_strictness():
    # Valid
    assert ExerciseValidator.validate({"id": "1", "title": "t", "mission": {"context": "c", "mission": "m", "objective": "o"}, "evaluation_rules": []})[0] == True
    # Missing ID
    assert ExerciseValidator.validate({"title": "t", "mission": {"context": "c", "mission": "m", "objective": "o"}, "evaluation_rules": []})[0] == False
    # Missing Mission
    assert ExerciseValidator.validate({"id": "1", "title": "t", "evaluation_rules": []})[0] == False
    # Missing Title
    assert ExerciseValidator.validate({"id": "1", "mission": {"context": "c", "mission": "m", "objective": "o"}, "evaluation_rules": []})[0] == False
    # Invalid Rule type
    assert ExerciseValidator.validate({"id": "1", "title": "t", "mission": {"context": "c", "mission": "m", "objective": "o"}, "evaluation_rules": "not_a_list"})[0] == False
    # Missing Objective in Mission
    assert ExerciseValidator.validate({"id": "1", "title": "t", "mission": {"context": "c", "mission": "m"}, "evaluation_rules": []})[0] == False

def test_json_round_trip():
    data = {
        "id": "ex_rt",
        "title": "Round Trip",
        "difficulty": "BEGINNER",
        "mission": {
            "context": "ctx",
            "mission": "msn",
            "constraints": ["c1"],
            "objective": "obj"
        },
        "evaluation_rules": [{"id": "r1", "type": "topology"}],
        "skills": ["GPIO"]
    }
    ex = ExerciseLoader.load_from_dict(data)
    json_str = ex.to_json()
    re_data = json.loads(json_str)
    
    assert re_data["id"] == "ex_rt"
    assert re_data["mission"]["objective"] == "obj"
    assert re_data["difficulty"] == "BEGINNER"

def test_lifecycle_and_retry():
    engine = ExerciseEngine(EvaluationEngine(None), FeedbackEngine(), ProgressionEngine(AttemptRepository(), ProgressRepository()), DiagnosisEngine())
    ex = Exercise("1", "T", "S", ExerciseMission("c", "m", [], "o"), "BEGINNER")
    ex.evaluation_rules = [{"id": "r1", "type": "code_pin", "gpio": 2, "mode": "OUT", "weight": 10}]
    proj = ProjectModel()
    proj.set_main_code("") # Clear the default code so the rule actually fails
    
    # Lifecycle
    assert engine.state == ExerciseState.NOT_STARTED
    engine.start_exercise(ex, proj)
    assert engine.state == ExerciseState.IN_PROGRESS
    
    engine.submit_exercise()
    # It will fail because the rule is not met
    assert engine.state == ExerciseState.FAILED
    
    # Retry keeps project
    engine.current_project.name = "Modified"
    engine.retry_exercise()
    assert engine.state == ExerciseState.IN_PROGRESS
    assert engine.current_project.name == "Modified"
    
    # Reset restores project
    engine.reset_exercise(proj)
    assert engine.current_project.name == proj.name

def test_student_isolation():
    repo_att = AttemptRepository()
    repo_prog = ProgressRepository()
    eng1 = ExerciseEngine(EvaluationEngine(None), FeedbackEngine(), ProgressionEngine(repo_att, repo_prog), DiagnosisEngine())
    eng2 = ExerciseEngine(EvaluationEngine(None), FeedbackEngine(), ProgressionEngine(repo_att, repo_prog), DiagnosisEngine())
    
    eng1.student_id = "student_A"
    eng2.student_id = "student_B"
    
    ex = Exercise("1", "T", "S", ExerciseMission("c", "m", [], "o"), "BEGINNER", skills=["GPIO"])
    eng1.start_exercise(ex, ProjectModel())
    eng2.start_exercise(ex, ProjectModel())
    
    eng1.submit_exercise()
    
    assert len(repo_att.get_attempts_for_exercise("student_A", "1")) == 1
    assert len(repo_att.get_attempts_for_exercise("student_B", "1")) == 0
    assert repo_prog.get_progress("student_A", "GPIO").attempts == 1
    assert repo_prog.get_progress("student_B", "GPIO").attempts == 0

def test_no_automatic_correction():
    engine = ExerciseEngine(EvaluationEngine(None), FeedbackEngine(), ProgressionEngine(AttemptRepository(), ProgressRepository()), DiagnosisEngine())
    ex = Exercise("1", "T", "S", ExerciseMission("c", "m", [], "o"), "BEGINNER")
    
    proj = ProjectModel()
    proj.components.append(ComponentModel(id="led1", type="led"))
    
    engine.start_exercise(ex, proj)
    engine.submit_exercise()
    
    # Ensure components list was not modified or auto-corrected
    assert len(engine.current_project.components) == 1
    assert engine.current_project.components[0].id == "led1"

def test_chaos_operations():
    engine = ExerciseEngine(EvaluationEngine(None), FeedbackEngine(), ProgressionEngine(AttemptRepository(), ProgressRepository()), DiagnosisEngine())
    ex1 = Exercise("1", "T", "S", ExerciseMission("c", "m", [], "o"), "BEGINNER")
    ex2 = Exercise("2", "T2", "S2", ExerciseMission("c", "m", [], "o"), "INTERMEDIATE")
    
    proj = ProjectModel()
    
    # Randomly perform 1000 operations
    for _ in range(1000):
        op = random.choice(["start1", "start2", "submit", "retry", "reset", "hint"])
        if op == "start1":
            engine.start_exercise(ex1, proj)
        elif op == "start2":
            engine.start_exercise(ex2, proj)
        elif op == "submit" and engine.current_exercise:
            engine.submit_exercise()
        elif op == "retry":
            engine.retry_exercise()
        elif op == "reset" and engine.current_exercise:
            engine.reset_exercise(proj)
        elif op == "hint":
            engine.request_hint()
            
    # Should complete without crashing
    assert True


from esp32_lab.application.education.exercises.models import LearningPath

def test_learning_path_methods():

    path = LearningPath('path_1', 'Fund', ['ex1', 'ex2', 'ex3'])

    assert path.next_exercise('ex1') == 'ex2'

    assert path.next_exercise('ex3') is None

    assert path.previous_exercise('ex2') == 'ex1'

    assert path.completion_percentage([]) == 0.0

    assert path.completion_percentage(['ex1', 'ex2', 'ex3']) == 100.0

    assert path.is_available('ex1', []) is True

    assert path.is_available('ex2', []) is False

    assert path.is_available('ex2', ['ex1']) is True

