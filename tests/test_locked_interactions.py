import pytest
from PySide6.QtWidgets import QApplication, QGraphicsItem
from PySide6.QtCore import Qt, QPointF
from esp32_lab.ui.canvas.circuit_scene import CircuitScene
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.models.component import ComponentModel
from esp32_lab.core.app_state import AppState, AppMode
from esp32_lab.application.education.interaction_policy import InteractionPolicy

@pytest.fixture
def scene():
    app_state = AppState()
    policy = InteractionPolicy(app_state)
    s = CircuitScene(interaction_policy=policy)
    s._test_app_state = app_state 
    return s

def test_unlocked_component_drag_rotate_delete(scene):
    project = ProjectModel()
    project.components.append(ComponentModel(id="led_1", type="led", x=0, y=0, properties={}))
    scene.load_project_circuit(project)
    scene._update_all_interaction_flags()
    item = scene.component_items["led_1"]
    
    assert item.flags() & QGraphicsItem.ItemIsMovable
    
    item.setSelected(True)
    initial_rot = item.rotation()
    scene.rotate_selected_component(90.0)
    assert item.rotation() != initial_rot
    
    scene.delete_selected_items()
    assert "led_1" not in scene.component_items

def test_locked_component_drag_rotate_delete(scene):
    project = ProjectModel(pedagogy_profile={
        "locked_elements": {
            "components": [{
                "id": "led_1",
                "locks": {"move": True, "rotate": True, "delete": True}
            }]
        }
    })
    project.components.append(ComponentModel(id="led_1", type="led", x=0, y=0, properties={}))
    scene.load_project_circuit(project)
    scene._update_all_interaction_flags()
    
    item = scene.component_items["led_1"]
    
    assert not (item.flags() & QGraphicsItem.ItemIsMovable)
    
    item.setSelected(True)
    initial_rot = item.rotation()
    scene.rotate_selected_component(90.0)
    assert item.rotation() == initial_rot
    
    scene.delete_selected_items()
    assert "led_1" in scene.component_items

def test_teacher_mode_allows_locked_modifications(scene):
    project = ProjectModel(pedagogy_profile={
        "locked_elements": {
            "components": [{
                "id": "led_1",
                "locks": {"move": True, "delete": True}
            }]
        }
    })
    project.components.append(ComponentModel(id="led_1", type="led", x=0, y=0, properties={}))
    scene.load_project_circuit(project)
    scene._update_all_interaction_flags()
    item = scene.component_items["led_1"]
    
    assert not (item.flags() & QGraphicsItem.ItemIsMovable)
    
    scene._test_app_state.activate_teacher_mode()
    
    assert item.flags() & QGraphicsItem.ItemIsMovable
    item.setSelected(True)
    scene.delete_selected_items()
    assert "led_1" not in scene.component_items
