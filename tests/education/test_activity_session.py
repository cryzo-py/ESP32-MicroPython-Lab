# -*- coding: utf-8 -*-
import pytest
import json
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.models.pedagogical_activity import create_default_activity, ActivityType
from esp32_lab.core.models.activity_session import ActivitySession, SessionState, StudentIdentity
from esp32_lab.core.session_repository import SessionRepository
from esp32_lab.core.activity_session_service import ActivitySessionService
from esp32_lab.core.clock import FakeClock

class InMemorySessionRepository(SessionRepository):
    def __init__(self):
        self.sessions = {}
        self.projects = {}

    def save(self, session: ActivitySession, project_snapshot: str = None) -> None:
        self.sessions[session.session_id] = session.to_dict()
        if project_snapshot:
            self.projects[session.session_id] = project_snapshot

    def load(self, session_id: str) -> ActivitySession:
        return ActivitySession.from_dict(self.sessions.get(session_id))

    def get_working_project(self, session_id: str) -> str:
        return self.projects.get(session_id)

    def find_active_session(self, activity_id: str, student_id: str = "") -> ActivitySession:
        for sess_dict in self.sessions.values():
            if sess_dict["activity_id"] == activity_id:
                if not student_id or (sess_dict.get("student") and sess_dict["student"].get("student_id") == student_id):
                    return ActivitySession.from_dict(sess_dict)
        return None

@pytest.fixture
def repo():
    return InMemorySessionRepository()

@pytest.fixture
def clock():
    return FakeClock(1000)

@pytest.fixture
def service(repo, clock):
    return ActivitySessionService(repo, clock)

def create_subject(act_type=ActivityType.TP, duration=60, strict=False):
    act = create_default_activity(act_type)
    act["id"] = "act_123"
    act["duration_minutes"] = duration
    act["settings"]["strict_mode"] = strict
    proj = ProjectModel()
    proj.pedagogy_profile = {"activity": act}
    return proj

def test_creation_session(service):
    proj = create_subject()
    sess, work_proj = service.load_or_create_session(proj)
    assert sess.status == SessionState.NOT_STARTED
    assert sess.activity_id == "act_123"
    # Subject shouldn't be modified
    assert work_proj is not proj

def test_start_transition(service, clock):
    proj = create_subject(duration=60)
    sess, _ = service.load_or_create_session(proj)
    service.start_session()
    
    assert sess.status == SessionState.IN_PROGRESS
    assert sess.started_at == 1000
    assert sess.deadline == 1000 + 3600

def test_activity_without_duration(service):
    proj = create_subject(duration=0)
    sess, _ = service.load_or_create_session(proj)
    service.start_session()
    assert sess.deadline is None
    assert sess.status == SessionState.IN_PROGRESS

def test_remaining_time(service, clock):
    proj = create_subject(duration=60)
    service.load_or_create_session(proj)
    service.start_session()
    
    clock.advance(1800) # 30 mins
    rem = service.update_and_get_remaining_time()
    assert rem == 1800
    assert service.get_session().status == SessionState.IN_PROGRESS

def test_expiration_and_freeze(service, clock):
    proj = create_subject(duration=60)
    service.load_or_create_session(proj)
    service.start_session()
    
    clock.advance(4000) # Past 60 mins
    rem = service.update_and_get_remaining_time()
    assert rem == 0
    
    sess = service.get_session()
    # It first goes to EXPIRED, then freeze_session makes it FROZEN
    assert sess.status == SessionState.FROZEN

def test_persistence_and_restoration(service, repo, clock):
    proj = create_subject(duration=60)
    student = StudentIdentity("stu1")
    sess, work = service.load_or_create_session(proj, student)
    service.start_session()
    clock.advance(1000)
    
    # Simulate app restart
    service2 = ActivitySessionService(repo, clock)
    sess2, work2 = service2.load_or_create_session(proj, student)
    
    assert sess2.session_id == sess.session_id
    assert sess2.status == SessionState.IN_PROGRESS
    assert sess2.started_at == sess.started_at

def test_restoration_already_expired(service, repo, clock):
    proj = create_subject(duration=60)
    student = StudentIdentity("stu1")
    sess, _ = service.load_or_create_session(proj, student)
    service.start_session()
    
    clock.advance(5000) # Expired while closed
    
    service2 = ActivitySessionService(repo, clock)
    sess2, _ = service2.load_or_create_session(proj, student)
    service2.update_and_get_remaining_time()
    
    assert sess2.status == SessionState.FROZEN

def test_exam_requires_identity(service):
    proj = create_subject(ActivityType.EXAM, strict=True)
    with pytest.raises(ValueError, match="identit.*requise"):
        service.load_or_create_session(proj)
        
    student = StudentIdentity("stu1")
    sess, _ = service.load_or_create_session(proj, student)
    assert sess.student.student_id == "stu1"

def test_manual_freeze(service):
    proj = create_subject()
    service.load_or_create_session(proj)
    service.start_session()
    service.request_freeze()
    assert service.get_session().status == SessionState.FROZEN
