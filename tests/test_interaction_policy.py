import pytest
from esp32_lab.core.app_state import AppState, AppMode
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.application.education.interaction_policy import InteractionPolicy

@pytest.fixture
def app_state():
    return AppState()

@pytest.fixture
def policy(app_state):
    return InteractionPolicy(app_state)

def test_normal_project(policy):
    project = ProjectModel()
    policy.load_from_project(project)
    
    assert policy.can_move("led_1")
    assert policy.can_delete("led_1")

def test_pedagogical_project_no_locks(policy):
    project = ProjectModel(pedagogy_profile={
        "locked_elements": {"components": []}
    })
    policy.load_from_project(project)
    
    assert policy.can_move("led_1")

def test_fully_locked_component(policy):
    project = ProjectModel(pedagogy_profile={
        "locked_elements": {
            "components": [{
                "id": "led_1",
                "locks": {
                    "move": True,
                    "delete": True,
                    "rotate": True,
                    "interact": True,
                    "properties": True
                }
            }]
        }
    })
    policy.load_from_project(project)
    
    assert not policy.can_move("led_1")
    assert not policy.can_delete("led_1")
    assert not policy.can_rotate("led_1")
    assert not policy.can_interact("led_1")
    assert not policy.can_edit_properties("led_1")

def test_partial_locks(policy):
    project = ProjectModel(pedagogy_profile={
        "locked_elements": {
            "components": [{
                "id": "btn_1",
                "locks": {
                    "move": True,
                    "interact": False
                }
            }]
        }
    })
    policy.load_from_project(project)
    
    assert not policy.can_move("btn_1")
    assert policy.can_interact("btn_1")

def test_teacher_mode_bypass(policy, app_state):
    project = ProjectModel(pedagogy_profile={
        "locked_elements": {
            "components": [{
                "id": "led_1",
                "locks": {"move": True}
            }]
        }
    })
    policy.load_from_project(project)
    
    assert not policy.can_move("led_1")
    app_state.activate_teacher_mode()
    assert policy.can_move("led_1")

def test_unknown_element(policy):
    project = ProjectModel(pedagogy_profile={
        "locked_elements": {"components": []}
    })
    policy.load_from_project(project)
    assert policy.can_move("ghost_1")

def test_multiple_components(policy):
    project = ProjectModel(pedagogy_profile={
        "locked_elements": {
            "components": [
                {"id": "led_1", "locks": {"move": True}},
                {"id": "led_2", "locks": {"move": False}}
            ]
        }
    })
    policy.load_from_project(project)
    
    assert not policy.can_move("led_1")
    assert policy.can_move("led_2")
