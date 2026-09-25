"""
Tests unitaires pour les modèles et le service de projet
"""

import tempfile
from pathlib import Path
import pytest

from esp32_lab.core.models.board import create_default_esp32_wroom
from esp32_lab.core.project_service import ProjectService


def test_board_definition():
    board = create_default_esp32_wroom()
    assert board.id == "esp32_wroom_32"
    assert board.has_wifi is True
    
    pin2 = board.get_pin(2)
    assert pin2 is not None
    assert pin2.name == "GPIO2"
    assert pin2.pwm_supported is True


def test_default_project_creation():
    project = ProjectService.create_default_project("Test Blink")
    assert project.name == "Test Blink"
    assert "main.py" in project.files
    assert len(project.components) == 3
    assert len(project.connections) == 3
    
    # Vérification des connexions (cavaliers réels à travers la platine)
    c1 = project.connections[0]
    assert c1.from_component == "esp32"
    assert c1.from_pin == "GPIO2"
    assert c1.to_component == "breadboard_1"


def test_save_and_load_project():
    project = ProjectService.create_default_project("SaveLoadTest")
    project.set_main_code("print('Hello Pytest')")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        save_path = Path(tmpdir) / "test_project.esp32lab"
        ProjectService.save_project(project, save_path)
        assert save_path.exists()
        
        loaded = ProjectService.load_project(save_path)
        assert loaded.name == "SaveLoadTest"
        assert loaded.get_main_code() == "print('Hello Pytest')"
        assert len(loaded.components) == 3
        assert len(loaded.connections) == 3
