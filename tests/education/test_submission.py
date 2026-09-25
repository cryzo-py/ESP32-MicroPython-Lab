# -*- coding: utf-8 -*-
import pytest
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.models.pedagogical_activity import create_default_activity, ActivityType
from esp32_lab.core.models.activity_session import SessionState, StudentIdentity
from esp32_lab.core.activity_session_service import ActivitySessionService
from esp32_lab.core.session_repository import SessionRepository
from esp32_lab.core.submission_repository import SubmissionRepository
from esp32_lab.core.clock import FakeClock
from esp32_lab.core.models.submission import SubmissionReason, SubmissionStatus

class InMemorySessionRepo(SessionRepository):
    def __init__(self):
        self.sessions = {}
        self.projects = {}
    def save(self, session, project_snapshot=None):
        self.sessions[session.session_id] = session.to_dict()
        if project_snapshot: self.projects[session.session_id] = project_snapshot
    def load(self, session_id): return None
    def get_working_project(self, session_id): return self.projects.get(session_id)
    def find_active_session(self, activity_id, student_id=""): return None

class InMemorySubmissionRepo(SubmissionRepository):
    def __init__(self):
        self.subs = {}
    def save(self, submission):
        self.subs[submission.submission_id] = submission.to_dict()
    def load(self, submission_id):
        return None
    def find_by_session(self, session_id):
        for s in self.subs.values():
            if s["session_id"] == session_id:
                from esp32_lab.core.models.submission import Submission
                return Submission.from_dict(s)
        return None

def create_subject():
    act = create_default_activity(ActivityType.TP)
    act["id"] = "act_456"
    act["duration_minutes"] = 10
    proj = ProjectModel()
    proj.pedagogy_profile = {"activity": act, "criteria": []}
    return proj

@pytest.fixture
def repos():
    return InMemorySessionRepo(), InMemorySubmissionRepo()

@pytest.fixture
def service(repos):
    sess_repo, sub_repo = repos
    clock = FakeClock(1000)
    return ActivitySessionService(sess_repo, clock, sub_repo)

def test_student_submit(service, repos):
    proj = create_subject()
    sess, _ = service.load_or_create_session(proj, StudentIdentity("student_1"))
    service.start_session()
    
    # User clicks valider
    service.request_freeze()
    
    assert sess.status == SessionState.FROZEN
    sub = repos[1].find_by_session(sess.session_id)
    assert sub is not None
    assert sub.submission_reason == SubmissionReason.STUDENT_SUBMIT
    assert sub.status == SubmissionStatus.WAITING_TEACHER

def test_timeout_auto_submit(service, repos):
    proj = create_subject()
    sess, _ = service.load_or_create_session(proj, StudentIdentity("student_1"))
    service.start_session()
    
    service.clock.advance(10 * 60 + 1) # passes deadline
    service.update_and_get_remaining_time() # triggers check
    
    assert sess.status == SessionState.FROZEN
    sub = repos[1].find_by_session(sess.session_id)
    assert sub is not None
    assert sub.submission_reason == SubmissionReason.TIMEOUT_AUTO_SUBMIT
    
def test_double_submit_ignored(service, repos):
    proj = create_subject()
    sess, _ = service.load_or_create_session(proj, StudentIdentity("student_1"))
    service.start_session()
    
    service.request_freeze()
    sub1 = repos[1].find_by_session(sess.session_id)
    
    service.request_freeze() # second submit
    assert len(repos[1].subs) == 1
    
def test_snapshot_independence(service, repos):
    proj = create_subject()
    sess, work_proj = service.load_or_create_session(proj, StudentIdentity("student_1"))
    service.start_session()
    
    # Change working project
    work_proj.set_main_code("print('hello')")
    service.request_freeze()
    
    sub = repos[1].find_by_session(sess.session_id)
    assert sub.snapshot["files"]["main.py"] == "print('hello')"
    
    # Original is intact
    assert proj.get_main_code() != "print('hello')"
