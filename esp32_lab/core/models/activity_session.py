# -*- coding: utf-8 -*-
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

class SessionState(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    EXPIRED = "expired"
    FROZEN = "frozen"
    # Future compatibility
    SUBMITTED = "submitted"
    AUTO_EVALUATED = "auto_evaluated"
    TEACHER_REVIEW = "teacher_review"
    VALIDATED = "validated"

@dataclass
class StudentIdentity:
    student_id: str
    last_name: str = ""
    first_name: str = ""
    class_name: str = ""
    
    def to_dict(self) -> dict:
        return {
            "student_id": self.student_id,
            "last_name": self.last_name,
            "first_name": self.first_name,
            "class_name": self.class_name
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'StudentIdentity':
        return StudentIdentity(
            student_id=data.get("student_id", ""),
            last_name=data.get("last_name", ""),
            first_name=data.get("first_name", ""),
            class_name=data.get("class_name", "")
        )

@dataclass
class ActivitySession:
    activity_id: str
    session_id: str = field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:8]}")
    student: Optional[StudentIdentity] = None
    status: SessionState = SessionState.NOT_STARTED
    started_at: Optional[float] = None
    deadline: Optional[float] = None
    last_saved_at: Optional[float] = None
    schema_version: int = 1

    def to_dict(self) -> dict:
        return {
            "activity_id": self.activity_id,
            "session_id": self.session_id,
            "student": self.student.to_dict() if self.student else None,
            "status": self.status.value,
            "started_at": self.started_at,
            "deadline": self.deadline,
            "last_saved_at": self.last_saved_at,
            "schema_version": self.schema_version
        }

    @staticmethod
    def from_dict(data: dict) -> 'ActivitySession':
        sess = ActivitySession(activity_id=data.get("activity_id", ""))
        sess.session_id = data.get("session_id", sess.session_id)
        
        student_data = data.get("student")
        if student_data:
            sess.student = StudentIdentity.from_dict(student_data)
            
        try:
            sess.status = SessionState(data.get("status", "not_started"))
        except ValueError:
            sess.status = SessionState.NOT_STARTED
            
        sess.started_at = data.get("started_at")
        sess.deadline = data.get("deadline")
        sess.last_saved_at = data.get("last_saved_at")
        sess.schema_version = data.get("schema_version", 1)
        return sess

class ActivityPermissionPolicy:
    """Policy restricting actions based on session state."""
    
    @staticmethod
    def can_edit(session: Optional[ActivitySession]) -> bool:
        if not session:
            return True # Normal mode or teacher
        return session.status == SessionState.IN_PROGRESS
        
    @staticmethod
    def can_access_resources(session: Optional[ActivitySession], is_exam: bool = False) -> bool:
        if is_exam and session and session.status == SessionState.IN_PROGRESS:
            return False # Exams restrict course/examples
        return True
