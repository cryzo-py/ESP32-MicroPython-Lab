import pytest
from esp32_lab.application.education.feedback.progression import ProgressionEngine, AttemptRepository, ProgressRepository
from esp32_lab.application.education.feedback.models import ExerciseAttempt

def test_progression_engine():
    attempt_repo = AttemptRepository()
    progress_repo = ProgressRepository()
    engine = ProgressionEngine(attempt_repo, progress_repo)
    
    attempt1 = ExerciseAttempt(student_id="student1", exercise_id="ex1", score=100, max_score=100, errors=[], hints_used=0, success=True)
    engine.record_attempt(attempt1, ["GPIO"])
    
    prog = progress_repo.get_progress("student1", "GPIO")
    assert prog.attempts == 1
    assert prog.successes == 1
    assert prog.mastery == "PRACTICING"
    
    attempt2 = ExerciseAttempt(student_id="student1", exercise_id="ex2", score=100, max_score=100, errors=[], hints_used=0, success=True)
    attempt3 = ExerciseAttempt(student_id="student1", exercise_id="ex3", score=100, max_score=100, errors=[], hints_used=0, success=True)
    
    engine.record_attempt(attempt2, ["GPIO"])
    engine.record_attempt(attempt3, ["GPIO"])
    
    prog = progress_repo.get_progress("student1", "GPIO")
    assert prog.successes == 3
    assert prog.mastery == "MASTERED"
