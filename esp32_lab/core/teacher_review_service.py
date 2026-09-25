# -*- coding: utf-8 -*-
from typing import List, Optional
import time
from .models.submission import Submission, TeacherReview, FinalGrade, SubmissionStatus
from .submission_repository import SubmissionRepository
from .app_state import AppState

class TeacherReviewService:
    def __init__(self, repo: SubmissionRepository, app_state: AppState):
        self.repo = repo
        self.app_state = app_state

    def submit_review(self, 
                      submission_id: str, 
                      score: float, 
                      comment: str = "", 
                      reason: str = "") -> Submission:
        if not self.app_state.is_teacher_mode_active():
            raise PermissionError("L'évaluation manuelle nécessite le mode enseignant actif.")
            
        submission = self.repo.load(submission_id)
        if not submission:
            raise ValueError("Soumission introuvable.")
            
        if not submission.proposed_grade:
            raise ValueError("Aucune note proposée à corriger.")
            
        final_grade = FinalGrade(
            score=score,
            max_score=submission.proposed_grade.max_score,
            percentage=(score / submission.proposed_grade.max_score * 100) if submission.proposed_grade.max_score > 0 else 100.0
        )
        
        # Teacher ID could be retrieved from AuthManager, but for simplicity here we use "teacher"
        teacher_id = "teacher"
        
        submission.teacher_review = TeacherReview(
            teacher_id=teacher_id,
            reviewed_at=time.time(),
            final_grade=final_grade,
            comment=comment,
            modification_reason=reason
        )
        submission.status = SubmissionStatus.FINALIZED
        
        self.repo.save(submission)
        return submission

    def get_activity_submissions(self, activity_id: str) -> List[Submission]:
        if not self.app_state.is_teacher_mode_active():
            raise PermissionError("Seul l'enseignant peut consulter les soumissions.")
        return self.repo.get_submissions_for_activity(activity_id)
