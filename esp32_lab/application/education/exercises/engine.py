import copy
from typing import Dict, Any, Optional
from .models import Exercise, ExerciseState
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.application.education.evaluation.engine import EvaluationEngine
from esp32_lab.application.education.feedback.feedback_engine import FeedbackEngine
from esp32_lab.application.education.feedback.progression import ProgressionEngine
from esp32_lab.application.education.feedback.diagnosis import DiagnosisEngine
from esp32_lab.application.education.feedback.models import ExerciseAttempt

class ExerciseEngine:
    """Orchestrates an exercise session, coupling Evaluation, Feedback, and Progression."""
    
    def __init__(self, eval_engine: EvaluationEngine, feedback_engine: FeedbackEngine, prog_engine: ProgressionEngine, diag_engine: DiagnosisEngine):
        self.eval_engine = eval_engine
        self.feedback_engine = feedback_engine
        self.prog_engine = prog_engine
        self.diag_engine = diag_engine
        
        self.current_exercise: Optional[Exercise] = None
        self.current_project: Optional[ProjectModel] = None
        self.student_id: str = "default_student"
        self.state: str = ExerciseState.NOT_STARTED
        self.attempt_count: int = 0
        self.hints_used: int = 0
        self.diagnoses = []
        self.feedbacks = []
        
    def start_exercise(self, exercise: Exercise, starter_project: ProjectModel):
        self.current_exercise = exercise
        self.current_project = copy.deepcopy(starter_project)
        self.state = ExerciseState.IN_PROGRESS
        self.attempt_count = 0
        self.hints_used = 0
        self.diagnoses = []
        self.feedbacks = []
        
    def request_hint(self):
        if self.current_exercise and self.state in [ExerciseState.IN_PROGRESS, ExerciseState.FAILED]:
            self.hints_used += 1
            
    def submit_exercise(self):
        if not self.current_exercise or not self.current_project:
            return
            
        self.state = ExerciseState.SUBMITTED
        self.attempt_count += 1
        
        # 1. Evaluate
        # Build EvaluationRules from dicts
        from esp32_lab.application.education.evaluation.models import EvaluationRule
        rules = []
        for rd in self.current_exercise.evaluation_rules:
            # simple mock deserialization
            rules.append(EvaluationRule(
                id=rd.get("id", "rule"),
                type=rd.get("type", "code_pin"),
                weight=rd.get("weight", 10),
                gpio=rd.get("gpio"),
                mode=rd.get("mode"),
                component_type=rd.get("component_type"),
                pin_name=rd.get("pin_name")
            ))
            
        # We simulate passing it to evaluation engine via a dummy lesson interface
        class DummyLesson:
            evaluation_rules = rules
        
        eval_items = self.eval_engine.evaluate(DummyLesson(), self.current_project)
        
        # 2. Diagnose
        self.diagnoses = self.diag_engine.diagnose(eval_items)
        successes = [item for item in eval_items if item.status == "PASS"]
        
        # 3. Feedback
        rule_meta = {rd.get("id"): rd for rd in self.current_exercise.evaluation_rules}
        self.feedbacks = self.feedback_engine.generate_feedbacks(self.diagnoses, successes, rule_meta)
        
        # Calculate Score
        total_score = sum(i.score for i in eval_items)
        max_score = sum(i.max_score for i in eval_items) if eval_items else 100
        success = (total_score == max_score and max_score > 0) or len(self.diagnoses) == 0
        
        if success:
            self.state = ExerciseState.PASSED
        else:
            self.state = ExerciseState.FAILED
            
        # 4. Record Attempt
        attempt = ExerciseAttempt(
            student_id=self.student_id,
            exercise_id=self.current_exercise.id,
            score=total_score,
            max_score=max_score,
            errors=[d.cause for d in self.diagnoses],
            hints_used=self.hints_used,
            success=success
        )
        self.prog_engine.record_attempt(attempt, self.current_exercise.skills)

    def retry_exercise(self):
        if self.state in [ExerciseState.FAILED, ExerciseState.PASSED]:
            self.state = ExerciseState.IN_PROGRESS
            # Project is NOT reset, errors are kept for reference, new attempt count keeps growing.
            
    def reset_exercise(self, starter_project: ProjectModel):
        # Reloads the initial starter project entirely
        self.current_project = copy.deepcopy(starter_project)
        self.state = ExerciseState.IN_PROGRESS
