from typing import List, Dict, Any, Optional
from .models import ExerciseAttempt, StudentProgress

class AttemptRepository:
    def __init__(self):
        self._attempts: List[ExerciseAttempt] = []
        
    def save(self, attempt: ExerciseAttempt):
        self._attempts.append(attempt)
        
    def get_attempts_for_exercise(self, student_id: str, exercise_id: str) -> List[ExerciseAttempt]:
        return [a for a in self._attempts if a.student_id == student_id and a.exercise_id == exercise_id]

class ProgressRepository:
    def __init__(self):
        self._progress: Dict[str, StudentProgress] = {}
        
    def get_progress(self, student_id: str, skill: str) -> StudentProgress:
        key = f"{student_id}_{skill}"
        if key not in self._progress:
            self._progress[key] = StudentProgress(student_id=student_id, skill=skill, mastery="NOT_STARTED")
        return self._progress[key]
        
    def save_progress(self, progress: StudentProgress):
        key = f"{progress.student_id}_{progress.skill}"
        self._progress[key] = progress

class ProgressionEngine:
    def __init__(self, attempt_repo: AttemptRepository, progress_repo: ProgressRepository):
        self.attempt_repo = attempt_repo
        self.progress_repo = progress_repo
        
    def record_attempt(self, attempt: ExerciseAttempt, skills_worked: List[str]):
        self.attempt_repo.save(attempt)
        
        for skill in skills_worked:
            progress = self.progress_repo.get_progress(attempt.student_id, skill)
            progress.attempts += 1
            if attempt.success:
                progress.successes += 1
            progress.last_attempt = attempt.timestamp
            
            # Simple mastery logic
            if progress.successes >= 3:
                progress.mastery = "MASTERED"
            elif progress.successes > 0:
                progress.mastery = "PRACTICING"
            else:
                progress.mastery = "LEARNING"
                
            self.progress_repo.save_progress(progress)
