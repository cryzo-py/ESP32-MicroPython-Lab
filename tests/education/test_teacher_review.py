# -*- coding: utf-8 -*-
import pytest
import time
from esp32_lab.core.models.submission import Submission, ProposedGrade, SubmissionStatus
from esp32_lab.core.submission_repository import SQLiteSubmissionRepository
from esp32_lab.core.teacher_review_service import TeacherReviewService
from esp32_lab.core.app_state import AppState

@pytest.fixture
def app_state():
    state = AppState()
    state.activate_teacher_mode()
    return state

@pytest.fixture
def repo(tmpdir):
    import os
    db_path = os.path.join(tmpdir, "sessions.db")
    return SQLiteSubmissionRepository(db_path)

@pytest.fixture
def service(repo, app_state):
    return TeacherReviewService(repo, app_state)

def create_mock_submission(repo, activity_id="a1", score=10.0, status=SubmissionStatus.WAITING_TEACHER):
    sub = Submission(session_id=f"sess_{time.time()}", activity_id=activity_id)
    sub.status = status
    sub.proposed_grade = ProposedGrade(score=score, max_score=20.0, percentage=(score/20.0)*100)
    sub.evaluation_result = {
        "status": "PARTIAL",
        "criteria": {
            "c1": {"result": "PASS"},
            "c2": {"result": "NOT_EVALUATED"}
        }
    }
    repo.save(sub)
    return sub

def test_accept_proposed_grade(service, repo):
    sub = create_mock_submission(repo, score=15.0)
    
    rev_sub = service.submit_review(sub.submission_id, score=15.0, comment="Très bien")
    
    assert rev_sub.status == SubmissionStatus.FINALIZED
    assert rev_sub.teacher_review is not None
    assert rev_sub.teacher_review.final_grade.score == 15.0
    assert rev_sub.proposed_grade.score == 15.0
    assert rev_sub.teacher_review.comment == "Très bien"

def test_modify_proposed_grade_and_audit(service, repo):
    sub = create_mock_submission(repo, score=10.0)
    
    rev_sub = service.submit_review(sub.submission_id, score=12.0, comment="J'ajoute 2 points", reason="NOT_EVALUATED était correct")
    
    # Conservation of proposed grade
    assert rev_sub.proposed_grade.score == 10.0
    # Final grade
    assert rev_sub.teacher_review.final_grade.score == 12.0
    assert rev_sub.teacher_review.modification_reason == "NOT_EVALUATED était correct"

def test_student_access_denied(service, repo, app_state):
    sub = create_mock_submission(repo)
    
    app_state.leave_teacher_mode() # Becomes student
    assert not app_state.is_teacher_mode_active()
    
    with pytest.raises(PermissionError):
        service.submit_review(sub.submission_id, score=20.0)
        
    with pytest.raises(PermissionError):
        service.get_activity_submissions("a1")

def test_sqlite_persistence_and_restore(service, repo, tmpdir, app_state):
    sub = create_mock_submission(repo, score=14.0)
    service.submit_review(sub.submission_id, score=16.0, comment="Bravo")
    
    # New instance to simulate restart
    import os
    db_path = os.path.join(tmpdir, "sessions.db")
    repo2 = SQLiteSubmissionRepository(db_path)
    service2 = TeacherReviewService(repo2, app_state)
    
    subs = service2.get_activity_submissions("a1")
    assert len(subs) == 1
    restored = subs[0]
    
    assert restored.status == SubmissionStatus.FINALIZED
    assert restored.teacher_review.final_grade.score == 16.0
    assert restored.proposed_grade.score == 14.0

def test_double_validation(service, repo):
    sub = create_mock_submission(repo, score=10.0)
    service.submit_review(sub.submission_id, score=12.0)
    
    # Second review should override and update audit
    rev_sub = service.submit_review(sub.submission_id, score=14.0, comment="Finalement 14")
    assert rev_sub.teacher_review.final_grade.score == 14.0
    assert rev_sub.proposed_grade.score == 10.0

def test_not_evaluated_handling(service, repo):
    # NOT_EVALUATED does not fail the auto-eval implicitly if handled by teacher
    sub = create_mock_submission(repo, score=10.0)
    assert sub.evaluation_result["criteria"]["c2"]["result"] == "NOT_EVALUATED"
    
    # Teacher validates the not_evaluated criterion manually
    rev = service.submit_review(sub.submission_id, score=20.0, reason="C2 est correct")
    assert rev.teacher_review.final_grade.score == 20.0
