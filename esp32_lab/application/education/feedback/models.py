import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class FeedbackMessage:
    id: str
    category: str # CODE, COMPONENT, PLACEMENT, PIN, TOPOLOGY, CONFIGURATION, BEHAVIOR
    severity: str # INFO, WARNING, ERROR, SUCCESS
    title: str
    message: str
    technical_explanation: str
    pedagogical_explanation: str
    related_rule: str
    hint_level: int = 0
    hints_available: int = 3
    hints_text: List[str] = field(default_factory=list)
    related_component: Optional[str] = None
    related_gpio: Optional[int] = None

@dataclass
class ErrorDiagnosis:
    category: str
    cause: str
    evidence: str
    priority: int
    rule_id: str

@dataclass
class ExerciseAttempt:
    student_id: str
    exercise_id: str
    score: int
    max_score: int
    errors: List[str]
    hints_used: int
    success: bool
    attempt_id: str = "attempt_0"
    timestamp: float = field(default_factory=time.time)
    duration: int = 0
    completed: bool = True

@dataclass
class StudentProgress:
    student_id: str
    skill: str
    mastery: str # NOT_STARTED, LEARNING, PRACTICING, MASTERED
    attempts: int = 0
    successes: int = 0
    last_attempt: float = 0.0
