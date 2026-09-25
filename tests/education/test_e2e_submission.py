# -*- coding: utf-8 -*-
import pytest
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.models.component import ComponentModel
from esp32_lab.core.models.pedagogical_activity import create_default_activity, ActivityType
from esp32_lab.core.models.activity_session import StudentIdentity, SessionState
from esp32_lab.core.activity_session_service import ActivitySessionService
from esp32_lab.core.session_repository import SQLiteSessionRepository
from esp32_lab.core.submission_repository import SQLiteSubmissionRepository
from esp32_lab.core.clock import FakeClock
from esp32_lab.core.models.submission import SubmissionReason, SubmissionStatus
from esp32_lab.core.teacher_review_service import TeacherReviewService
from esp32_lab.core.app_state import AppState
import tempfile
from pathlib import Path

def setup_repos(tmpdir):
    sess_db = Path(tmpdir) / "sessions.db"
    sess_repo = SQLiteSessionRepository(sess_db)
    sub_repo = SQLiteSubmissionRepository(sess_db)
    return sess_repo, sub_repo

def test_e2e_submission(tmpdir):
    # 1. Create Teacher's Subject (Activity + SuccessProfile)
    act = create_default_activity(ActivityType.TP)
    act["duration_minutes"] = 30
    
    pedagogy_profile = {
        "activity": act,
        "criteria": [
            {
                "id": "c1",
                "type": "required_component",
                "blocking": True,
                "expected": {"type": "Potentiometer", "count": 1}
            },
            {
                "id": "c2",
                "type": "code_pin_mode",
                "expected": {"gpio": 34, "mode": "IN"}
            },
            {
                "id": "c3",
                "type": "code_pin_mode",
                "expected": {"gpio": 18, "mode": "OUT"}
            }
        ]
    }
    
    subject = ProjectModel()
    subject.pedagogy_profile = pedagogy_profile
    
    # 2. Student starts Session
    sess_repo, sub_repo = setup_repos(tmpdir)
    clock = FakeClock(1000)
    service = ActivitySessionService(sess_repo, clock, sub_repo)
    
    sess, work_proj = service.load_or_create_session(subject, StudentIdentity("student_99"))
    service.start_session()
    
    assert sess.status == SessionState.IN_PROGRESS
    
    # 3. Student makes modifications
    pot = ComponentModel(type="Potentiometer", id="pot_1", x=0, y=0)
    work_proj.components.append(pot)
    work_proj.set_main_code("from machine import Pin\nadc = Pin(34, Pin.IN)\npwm = Pin(18, Pin.OUT)")
    
    # 4. Student Submits
    service.request_freeze()
    assert sess.status == SessionState.FROZEN
    
    # 5. Verify Submission & Evaluation
    sub = sub_repo.find_by_session(sess.session_id)
    assert sub.status == SubmissionStatus.WAITING_TEACHER
    assert sub.evaluation_result["status"] == "SUCCESS"
    assert sub.proposed_grade.percentage == 100.0
    
    # 6. Teacher Review
    app_state = AppState()
    app_state.activate_teacher_mode()
    teacher_service = TeacherReviewService(sub_repo, app_state)
    
    rev = teacher_service.submit_review(sub.submission_id, score=90.0, comment="Très bien mais tu peux améliorer le code", reason="Pénalité de lisibilité")
    
    assert rev.status == SubmissionStatus.FINALIZED
    assert rev.teacher_review.final_grade.score == 90.0
    assert rev.proposed_grade.percentage == 100.0 # Proposed is immutable
    
    # 7. Verify Persistence
    sess_repo2, sub_repo2 = setup_repos(tmpdir)
    teacher_service2 = TeacherReviewService(sub_repo2, app_state)
    subs = teacher_service2.get_activity_submissions(act["id"])
    assert len(subs) == 1
    sub2 = subs[0]
    
    assert sub2.status == SubmissionStatus.FINALIZED
    assert sub2.teacher_review.comment == "Très bien mais tu peux améliorer le code"
