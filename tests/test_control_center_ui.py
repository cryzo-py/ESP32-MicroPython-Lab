import pytest
from PySide6.QtWidgets import QApplication
from esp32_lab.ui.main_window import MainWindow
from esp32_lab.core.app_state import AppMode

@pytest.fixture
def main_window(app):
    win = MainWindow()
    win.show()
    return win

def test_dock_visibility(main_window):
    # 1. dock absent en STUDENT
    assert not main_window.control_center_dock.isVisible()
    
    # 2. dock disponible en TEACHER
    app_state = main_window.circuit_scene.interaction_policy._app_state
    app_state.activate_teacher_mode()
    assert main_window.control_center_dock.isVisible()

def test_mission_editing(main_window):
    app_state = main_window.circuit_scene.interaction_policy._app_state
    app_state.activate_teacher_mode()
    
    # 3. création d'une mission
    mission_tab = main_window.control_center_dock.mission_tab
    mission_tab.edit_title.setText("My TP")
    mission_tab.edit_desc.setPlainText("Do this")
    
    project = main_window.current_project
    assert project.pedagogy_profile is not None
    assert project.pedagogy_profile["mission"]["title"] == "My TP"
    assert project.pedagogy_profile["mission"]["description"] == "Do this"
    
def test_criteria_management(main_window):
    app_state = main_window.circuit_scene.interaction_policy._app_state
    app_state.activate_teacher_mode()
    
    # Simulating criteria dialog addition is hard directly, 
    # but we can modify the project and test the UI reload.
    project = main_window.current_project
    project.pedagogy_profile = {
        "criteria": [
            {"id": "topo_1", "category": "topology", "description": "LED connected", "enabled": True, "blocking": True},
            {"id": "code_1", "category": "code", "description": "Use PWM", "enabled": False, "blocking": False}
        ]
    }
    
    main_window.control_center_dock.load_project(project)
    
    criteria_tab = main_window.control_center_dock.criteria_tab
    
    topo_root = criteria_tab.roots["topology"]
    assert topo_root.childCount() == 1
    assert "LED connected" in topo_root.child(0).text(0)
    assert "☑" in topo_root.child(0).text(0)
    assert "[OBLIG]" in topo_root.child(0).text(0)
    
    code_root = criteria_tab.roots["code"]
    assert code_root.childCount() == 1
    assert "☐" in code_root.child(0).text(0)
    assert "[REC]" in code_root.child(0).text(0)

def test_tests_management(main_window):
    project = main_window.current_project
    project.pedagogy_profile = {
        "teacher_tests": [
            {"id": "test_1", "name": "Valid setup", "expected_outcome": "SUCCESS", "patches": []},
            {"id": "test_2", "name": "Invalid setup", "expected_outcome": "FAILURE", "patches": [{"op": "disconnect"}]}
        ]
    }
    main_window.control_center_dock.load_project(project)
    tests_tab = main_window.control_center_dock.tests_tab
    
    assert tests_tab.list_tests.count() == 2
    assert "✓" in tests_tab.list_tests.item(0).text()
    assert "✗" in tests_tab.list_tests.item(1).text()
