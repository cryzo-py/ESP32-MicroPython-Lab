import pytest
from esp32_lab.application.education.exercises.engine import ExerciseEngine
from esp32_lab.application.education.exercises.models import ExerciseState, Exercise, ExerciseMission
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.application.education.evaluation.engine import EvaluationEngine
from esp32_lab.application.education.feedback.feedback_engine import FeedbackEngine
from esp32_lab.application.education.feedback.diagnosis import DiagnosisEngine
from esp32_lab.application.education.feedback.progression import ProgressionEngine, AttemptRepository, ProgressRepository

def test_exercise_engine_workflow():
    eval_eng = EvaluationEngine(net_resolver=None)
    fb_eng = FeedbackEngine()
    prog_eng = ProgressionEngine(AttemptRepository(), ProgressRepository())
    diag_eng = DiagnosisEngine()
    
    engine = ExerciseEngine(eval_eng, fb_eng, prog_eng, diag_eng)
    
    mission = ExerciseMission("ctx", "mis", [], "obj")
    ex = Exercise("ex1", "Title", "Sum", mission, "BEGINNER")
    proj = ProjectModel()
    
    # Start
    engine.start_exercise(ex, proj)
    assert engine.state == ExerciseState.IN_PROGRESS
    
    # Hint
    engine.request_hint()
    assert engine.hints_used == 1
    
    # Submit
    engine.submit_exercise()
    assert engine.state in [ExerciseState.PASSED, ExerciseState.FAILED]
    assert engine.attempt_count == 1
    
    # Retry
    engine.retry_exercise()
    assert engine.state == ExerciseState.IN_PROGRESS
    
    # Reset
    engine.reset_exercise(proj)
    assert engine.state == ExerciseState.IN_PROGRESS
