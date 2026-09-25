import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPointF
from esp32_lab.ui.main_window import MainWindow
from esp32_lab.core.app_state import AppMode
from esp32_lab.core.models.component import ComponentModel

@pytest.fixture
def main_window(app):
    win = MainWindow()
    win.show()
    
    return win

def test_cadenas_visibility_modes(main_window):
    # 1. indisponible en STUDENT
    assert not main_window.teacher_toolbar.isVisible()
    
    # 2. disponible en TEACHER
    app_state = main_window.circuit_scene.interaction_policy._app_state
    app_state.activate_teacher_mode()
    assert main_window.teacher_toolbar.isVisible()
    
    # 10. retour STUDENT
    app_state.leave_teacher_mode()
    assert not main_window.teacher_toolbar.isVisible()
    assert not main_window.circuit_scene.is_lock_tool_active

def test_lock_tool_workflow(main_window):
    # Add a component
    project = main_window.current_project
    project.components.append(ComponentModel(id="led_1", type="led", x=0, y=0, properties={}))
    main_window.circuit_scene.load_project_circuit(project)
    
    app_state = main_window.circuit_scene.interaction_policy._app_state
    app_state.activate_teacher_mode()
    
    # Enable tool
    main_window.act_lock_tool.setChecked(True)
    main_window._toggle_lock_tool(True)
    assert main_window.circuit_scene.is_lock_tool_active
    
    # Simulate clicking on the LED in the scene
    item = main_window.circuit_scene.component_items["led_1"]
    
    # Normally this opens a dialog. In test, we can mock _open_lock_dialog or invoke it directly
    # To avoid blocking UI, we just check if it would be called or call the internals.
    main_window.circuit_view._open_lock_dialog = lambda comp_id: None  # mock
    
    # Just check if interaction policy updates correctly when saved
    if project.pedagogy_profile is None:
        project.pedagogy_profile = {"locked_elements": {"components": []}}
    project.pedagogy_profile["locked_elements"]["components"].append({
        "id": "led_1",
        "locks": {"move": True, "delete": True, "rotate": False, "interact": True, "properties": True}
    })
    
    # 11. sauvegarde / rechargement
    main_window.circuit_scene.interaction_policy.load_from_project(project)
    
    # Test permissions
    policy = main_window.circuit_scene.interaction_policy
    # In TEACHER mode, everything is allowed (bypass)
    assert policy.can_move("led_1")
    
    # 10. Retour student
    app_state.leave_teacher_mode()
    assert not policy.can_move("led_1")
    assert not policy.can_delete("led_1")
    assert policy.can_rotate("led_1")  # Not locked
    
def test_normal_project_no_restrictions(main_window):
    # 13. projet normal sans restrictions
    project = main_window.current_project
    project.pedagogy_profile = None
    project.components.append(ComponentModel(id="btn_1", type="button", x=0, y=0, properties={}))
    main_window.circuit_scene.load_project_circuit(project)
    
    policy = main_window.circuit_scene.interaction_policy
    assert policy.can_move("btn_1")
    assert policy.can_delete("btn_1")
