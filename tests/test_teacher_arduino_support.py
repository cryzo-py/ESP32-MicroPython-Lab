from unittest.mock import MagicMock, patch
import pytest

from PySide6.QtWidgets import QApplication
from esp32_lab.ui.dialogs.activity_wizard import ActivityWizardDialog
from esp32_lab.ui.main_window import MainWindow
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.core.models.component import ComponentModel
from esp32_lab.core.models.connection import ConnectionModel
from esp32_lab.core.courses import Lesson
from esp32_lab.core.evaluator import ExerciseEvaluator


@pytest.fixture(scope="session")
def app():
    instance = QApplication.instance()
    if not instance:
        instance = QApplication([])
    return instance


def test_activity_wizard_dialog_board_selection(app):
    dlg = ActivityWizardDialog()
    assert hasattr(dlg, "cb_board")
    
    # Par défaut : ESP32 DevKit V1
    data = dlg.get_activity_data()
    assert data["board_id"] == "esp32_wroom_32"
    assert data["language"] == "micropython"

    # Sélection Arduino Uno
    idx = dlg.cb_board.findData("arduino_uno")
    assert idx >= 0
    dlg.cb_board.setCurrentIndex(idx)
    data = dlg.get_activity_data()
    assert data["board_id"] == "arduino_uno"
    assert data["language"] == "arduino"

    # Recharger avec load_data
    dlg.load_data({"title": "TP Uno C++", "board_id": "arduino_uno", "duration": 45})
    assert dlg.txt_title.text() == "TP Uno C++"
    assert dlg.cb_board.currentData() == "arduino_uno"


def test_main_window_start_activity_wizard_with_arduino(app):
    win = MainWindow(app_profile="teacher")
    mock_data = {
        "title": "TP Examen Arduino Uno",
        "type": "EXAM",
        "duration": 60,
        "max_score": 20,
        "board_id": "arduino_uno",
        "language": "arduino",
        "description": "Programmer une LED clignotante en C++ sur Arduino Uno."
    }

    with patch("esp32_lab.ui.dialogs.activity_wizard.ActivityWizardDialog.exec", return_value=True), \
         patch("esp32_lab.ui.dialogs.activity_wizard.ActivityWizardDialog.get_activity_data", return_value=mock_data):
        win._start_activity_wizard()

    assert win.current_project.board_id == "arduino_uno"
    assert win.current_project.language == "arduino"
    assert win.tabs.isTabEnabled(0) is False  # MicroPython tab is grayed out
    assert win.tabs.currentIndex() == 1      # C++ tab active


def test_exercise_evaluator_evaluates_arduino_c_project():
    lesson = Lesson(
        id="lesson_1_gpio_led",
        chapter_num=1,
        chapter_title="GPIO",
        title="TP 1 : LED Clignotante",
        summary="Clignotement",
        theory="Théorie",
        challenge="Faire clignoter la LED connectée au pin 2",
        required_components=["led"],
        target_pin=2
    )

    arduino_code = """
    void setup() {
        pinMode(2, OUTPUT);
    }
    void loop() {
        digitalWrite(2, HIGH);
        delay(500);
        digitalWrite(2, LOW);
        delay(500);
    }
    """

    proj = ProjectModel(
        name="TP1 Arduino",
        board_id="arduino_uno",
        language="arduino",
        files={"sketch.ino": arduino_code},
        components=[
            ComponentModel(id="led_1", type="led", name="LED Rouge", x=200, y=100)
        ],
        connections=[
            ConnectionModel(from_component="uno", from_pin="D2", to_component="led_1", to_pin="anode", color="green")
        ]
    )

    evaluator = ExerciseEvaluator()
    res = evaluator.evaluate(lesson, proj)

    assert res.score > 0
    assert any("C++" in c.title or "Arduino" in c.title for c in res.criteria)
    # Vérifier que la syntaxe et la logique sont validées
    c_syntax = next(c for c in res.criteria if c.id == "syntax")
    assert c_syntax.passed is True
    assert "C++" in c_syntax.title

    c_logic = next(c for c in res.criteria if c.id == "logic")
    assert c_logic.passed is True

    c_wiring = next(c for c in res.criteria if c.id == "wiring")
    assert c_wiring.passed is True
