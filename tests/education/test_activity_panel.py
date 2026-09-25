# -*- coding: utf-8 -*-
import pytest
from PySide6.QtWidgets import QApplication
from esp32_lab.ui.main_window import MainWindow
from esp32_lab.core.project_service import ProjectService
from esp32_lab.core.models.pedagogical_activity import create_default_activity, ActivityType
from esp32_lab.core.models.activity_session import SessionState, StudentIdentity
from esp32_lab.core.activity_session_service import ActivitySessionService
from esp32_lab.core.clock import FakeClock

class DummyRepo:
    def find_active_session(self, a, s): return None
    def save(self, *args): pass
    def get_working_project(self, s): return None

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.fixture
def main_window(qapp):
    window = MainWindow()
    yield window
    window.close()

def is_visible(widget):
    return not widget.isHidden()

def test_normal_project_panel_invisible(main_window):
    project = ProjectService.create_empty_project()
    main_window._load_project(project)
    assert hasattr(main_window, "activity_panel")
    assert not is_visible(main_window.activity_panel)

def setup_panel(main_window, proj, is_teacher=False):
    repo = DummyRepo()
    clock = FakeClock()
    srv = ActivitySessionService(repo, clock)
    if proj.pedagogy_profile and "activity" in proj.pedagogy_profile:
        # Load session to populate srv.current_session
        srv.load_or_create_session(proj, StudentIdentity("test"))
    main_window.activity_panel.attach_service(srv, is_teacher=is_teacher)
    main_window._load_project(proj)
    return srv

def test_tp_panel_visible(main_window):
    project = ProjectService.create_empty_project()
    project.pedagogy_profile = {"activity": create_default_activity(ActivityType.TP)}
    setup_panel(main_window, project)
    assert is_visible(main_window.activity_panel)
    assert "TP" in main_window.activity_panel.lbl_header.text()

def test_exercise_panel_visible(main_window):
    project = ProjectService.create_empty_project()
    project.pedagogy_profile = {"activity": create_default_activity(ActivityType.EXERCISE)}
    setup_panel(main_window, project)
    assert is_visible(main_window.activity_panel)
    assert "EXERCICE" in main_window.activity_panel.lbl_header.text()

def test_exam_panel_visible(main_window):
    project = ProjectService.create_empty_project()
    project.pedagogy_profile = {"activity": create_default_activity(ActivityType.EXAM)}
    setup_panel(main_window, project)
    assert is_visible(main_window.activity_panel)
    assert "EXAMEN" in main_window.activity_panel.lbl_header.text()

def test_display_mission_title(main_window):
    project = ProjectService.create_empty_project()
    project.pedagogy_profile = {
        "activity": create_default_activity(ActivityType.TP),
        "mission": {"title": "Test Title"}
    }
    setup_panel(main_window, project)
    assert main_window.activity_panel.lbl_title.text() == "Test Title"

def test_display_duration_teacher(main_window):
    project = ProjectService.create_empty_project()
    act = create_default_activity(ActivityType.TP)
    act["duration_minutes"] = 45
    project.pedagogy_profile = {"activity": act}
    setup_panel(main_window, project, is_teacher=True)
    assert is_visible(main_window.activity_panel.lbl_duration)
    assert "45" in main_window.activity_panel.lbl_duration.text()

def test_hide_hints_if_not_allowed(main_window):
    project = ProjectService.create_empty_project()
    act = create_default_activity(ActivityType.EXAM) # exam has allow_hints=False
    project.pedagogy_profile = {
        "activity": act,
        "mission": {"hints": ["Hint 1"]}
    }
    setup_panel(main_window, project)
    assert not is_visible(main_window.activity_panel.lbl_hints)

def test_show_hints_if_allowed(main_window):
    project = ProjectService.create_empty_project()
    act = create_default_activity(ActivityType.TP) # tp has allow_hints=True
    project.pedagogy_profile = {
        "activity": act,
        "mission": {"hints": ["Hint 1"]}
    }
    setup_panel(main_window, project)
    assert is_visible(main_window.activity_panel.lbl_hints)
    assert "Hint 1" in main_window.activity_panel.lbl_hints.text()

def test_back_to_normal_project_hides_panel(main_window):
    project = ProjectService.create_empty_project()
    project.pedagogy_profile = {"activity": create_default_activity(ActivityType.TP)}
    setup_panel(main_window, project)
    assert is_visible(main_window.activity_panel)
    
    # Load normal project
    project2 = ProjectService.create_empty_project()
    main_window._load_project(project2)
    assert not is_visible(main_window.activity_panel)

def test_session_lifecycle_ui(main_window):
    project = ProjectService.create_empty_project()
    act = create_default_activity(ActivityType.TP)
    act["duration_minutes"] = 10
    project.pedagogy_profile = {"activity": act}
    
    srv = setup_panel(main_window, project, is_teacher=False)
    panel = main_window.activity_panel
    
    assert panel.btn_action.text() == "Commencer"
    panel.btn_action.click()
    
    assert srv.get_session().status == SessionState.IN_PROGRESS
    assert "Valider" in panel.btn_action.text()
    
    panel.btn_action.click() # user freezes early
    assert srv.get_session().status == SessionState.FROZEN
    assert not panel.btn_action.isVisible()
