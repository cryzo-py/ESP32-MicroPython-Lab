from typing import List, Optional
from PySide6.QtCore import QObject, Signal
from esp32_lab.application.education.exercises.catalog import ExerciseCatalog
from esp32_lab.application.education.exercises.engine import ExerciseEngine, ExerciseState
from esp32_lab.application.education.feedback.progression import ProgressionEngine
from esp32_lab.application.education.exercises.models import Exercise
from esp32_lab.core.project_service import ProjectService
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.application.education.feedback.models import FeedbackMessage

class ExerciseController(QObject):
    exercise_loaded = Signal(Exercise, ProjectModel)
    exercise_state_changed = Signal(str) # NOT_STARTED, IN_PROGRESS, SUBMITTED, PASSED, FAILED
    feedback_received = Signal(list)     # list[FeedbackMessage]
    hint_received = Signal(str, int)     # text, level
    progression_updated = Signal()
    
    def __init__(self, catalog: ExerciseCatalog, engine: ExerciseEngine, progression: ProgressionEngine):
        super().__init__()
        self.catalog = catalog
        self.engine = engine
        self.progression = progression
        self.current_student_id = "default_student"
        self._current_hints = []
        self._current_hint_level = 0
        
    def load_exercise(self, exercise_id: str):
        exercise = self.catalog.repository.get(exercise_id)
        if not exercise:
            return False
            
        # Create starter project from dict
        starter_dict = exercise.starter_project or {}
        project = ProjectModel()
        
        if starter_dict:
            if "components" in starter_dict:
                from esp32_lab.core.models.component import ComponentModel
                project.components = [ComponentModel.from_dict(c) for c in starter_dict["components"]]
            if "connections" in starter_dict:
                from esp32_lab.core.models.connection import ElectricalConnection
                project.connections = [ElectricalConnection.from_dict(c) for c in starter_dict["connections"]]
            if "files" in starter_dict:
                for filename, content in starter_dict["files"].items():
                    project.files[filename] = content
            else:
                project.files["main.py"] = ""
        else:
            project.files["main.py"] = ""
            
        self.engine.start_exercise(exercise, project)
        self._current_hints = []
        self._current_hint_level = 0
        
        self.exercise_loaded.emit(exercise, project)
        self.exercise_state_changed.emit(self.engine.state)
        return True
        
    def submit_exercise(self, current_project: ProjectModel):
        if not self.engine.current_exercise:
            return
            
        self.engine.current_project = current_project
        self.engine.submit_exercise()
        
        self.exercise_state_changed.emit(self.engine.state)
        
        if self.engine.state == ExerciseState.FAILED:
            feedbacks = getattr(self.engine, "feedbacks", [])
            self._current_hints = []
            for fb in feedbacks:
                if fb.hints_text:
                    self._current_hints.extend(fb.hints_text)
            self._current_hint_level = 0
            
            self.feedback_received.emit(feedbacks)
        elif self.engine.state == ExerciseState.PASSED:
            self.feedback_received.emit([])
            self.progression_updated.emit()
            
    def request_hint(self):
        if self._current_hint_level < len(self._current_hints):
            hint = self._current_hints[self._current_hint_level]
            self._current_hint_level += 1
            self.hint_received.emit(hint, self._current_hint_level)
            
    def retry_exercise(self):
        self.engine.retry_exercise()
        self.exercise_state_changed.emit(self.engine.state)
        
    def reset_exercise(self):
        if not self.engine.current_exercise:
            return
        self.load_exercise(self.engine.current_exercise.id)
        
    def is_unlocked(self, exercise_id: str) -> bool:
        exercise = self.catalog.repository.get(exercise_id)
        if not exercise:
            return False
            
        for pre in exercise.prerequisites:
            progress = self.progression.progress_repo.get_progress(self.current_student_id, pre.skill)
            if progress.mastery not in [pre.min_mastery, "MASTERED"]:
                if progress.successes == 0:
                    return False
        return True
        
    def is_mastered(self, exercise_id: str) -> bool:
        attempts = self.progression.attempt_repo.get_attempts_for_exercise(self.current_student_id, exercise_id)
        return any(a.success for a in attempts)
