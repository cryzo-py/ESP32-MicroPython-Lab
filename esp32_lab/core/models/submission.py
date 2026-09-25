# -*- coding: utf-8 -*-
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List

from .activity_session import StudentIdentity

class SubmissionReason(str, Enum):
    STUDENT_SUBMIT = "STUDENT_SUBMIT"
    TIMEOUT_AUTO_SUBMIT = "TIMEOUT_AUTO_SUBMIT"

class SubmissionStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    AUTO_EVALUATED = "AUTO_EVALUATED"
    WAITING_TEACHER = "WAITING_TEACHER"
    TEACHER_REVIEWED = "TEACHER_REVIEWED"
    FINALIZED = "FINALIZED"
    RETURNED = "RETURNED"

@dataclass
class ProposedGrade:
    score: float
    max_score: float
    percentage: float

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "max_score": self.max_score,
            "percentage": self.percentage
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'ProposedGrade':
        return ProposedGrade(
            score=data.get("score", 0.0),
            max_score=data.get("max_score", 0.0),
            percentage=data.get("percentage", 0.0)
        )

@dataclass
class FinalGrade:
    score: float
    max_score: float
    percentage: float

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "max_score": self.max_score,
            "percentage": self.percentage
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'FinalGrade':
        return FinalGrade(
            score=data.get("score", 0.0),
            max_score=data.get("max_score", 0.0),
            percentage=data.get("percentage", 0.0)
        )

@dataclass
class TeacherReview:
    teacher_id: str
    reviewed_at: float
    final_grade: FinalGrade
    comment: str = ""
    modification_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "teacher_id": self.teacher_id,
            "reviewed_at": self.reviewed_at,
            "final_grade": self.final_grade.to_dict(),
            "comment": self.comment,
            "modification_reason": self.modification_reason
        }

    @staticmethod
    def from_dict(data: dict) -> 'TeacherReview':
        return TeacherReview(
            teacher_id=data.get("teacher_id", ""),
            reviewed_at=data.get("reviewed_at", 0.0),
            final_grade=FinalGrade.from_dict(data.get("final_grade", {})),
            comment=data.get("comment", ""),
            modification_reason=data.get("modification_reason", "")
        )

@dataclass
class Submission:
    session_id: str
    activity_id: str
    student_identity: Optional[StudentIdentity] = None
    submission_id: str = field(default_factory=lambda: f"sub_{uuid.uuid4().hex[:8]}")
    submitted_at: Optional[float] = None
    submission_reason: SubmissionReason = SubmissionReason.STUDENT_SUBMIT
    status: SubmissionStatus = SubmissionStatus.SUBMITTED
    snapshot: Dict[str, Any] = field(default_factory=dict)
    evaluation_result: Dict[str, Any] = field(default_factory=dict)
    proposed_grade: Optional[ProposedGrade] = None
    teacher_review: Optional[TeacherReview] = None

    def to_dict(self) -> dict:
        return {
            "submission_id": self.submission_id,
            "session_id": self.session_id,
            "activity_id": self.activity_id,
            "student_identity": self.student_identity.to_dict() if self.student_identity else None,
            "submitted_at": self.submitted_at,
            "submission_reason": self.submission_reason.value,
            "status": self.status.value,
            "snapshot": self.snapshot,
            "evaluation_result": self.evaluation_result,
            "proposed_grade": self.proposed_grade.to_dict() if self.proposed_grade else None,
            "teacher_review": self.teacher_review.to_dict() if self.teacher_review else None
        }

    @staticmethod
    def from_dict(data: dict) -> 'Submission':
        sub = Submission(
            session_id=data.get("session_id", ""),
            activity_id=data.get("activity_id", "")
        )
        sub.submission_id = data.get("submission_id", sub.submission_id)
        if data.get("student_identity"):
            sub.student_identity = StudentIdentity.from_dict(data["student_identity"])
        sub.submitted_at = data.get("submitted_at")
        try:
            sub.submission_reason = SubmissionReason(data.get("submission_reason", "STUDENT_SUBMIT"))
        except ValueError:
            sub.submission_reason = SubmissionReason.STUDENT_SUBMIT
        try:
            sub.status = SubmissionStatus(data.get("status", "SUBMITTED"))
        except ValueError:
            sub.status = SubmissionStatus.SUBMITTED
            
        sub.snapshot = data.get("snapshot", {})
        sub.evaluation_result = data.get("evaluation_result", {})
        
        if data.get("proposed_grade"):
            sub.proposed_grade = ProposedGrade.from_dict(data["proposed_grade"])
            
        if data.get("teacher_review"):
            sub.teacher_review = TeacherReview.from_dict(data["teacher_review"])
            
        return sub
