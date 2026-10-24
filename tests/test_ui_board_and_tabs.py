"""
Tests pour la sélection de carte, les deux onglets de code et le grisement MicroPython (Commit 4).
"""

import time
import pytest
from PySide6.QtCore import Qt
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.ui.main_window import MainWindow


def test_main_window_dual_tabs_structure(app):
    win = MainWindow()
    assert win.tabs.count() == 2
    assert "main.py" in win.tabs.tabText(0)
    assert "sketch.ino" in win.tabs.tabText(1)
    win.close()


def test_main_window_switch_to_arduino_uno_griser(app):
    win = MainWindow()

    # Initialement sur ESP32 : les deux onglets sont actifs
    assert win.tabs.isTabEnabled(0) is True
    assert win.tabs.isTabEnabled(1) is True

    # Basculer vers Arduino Uno
    win._switch_board("arduino_uno")

    # L'onglet MicroPython doit être grisé (disabled)
    assert win.tabs.isTabEnabled(0) is False
    assert win.tabs.currentIndex() == 1  # Doit basculer sur l'onglet C++
    assert "MicroPython non supporté" in win.tabs.tabToolTip(0)

    # Basculer à nouveau vers ESP32
    win._switch_board("esp32_wroom_32")
    assert win.tabs.isTabEnabled(0) is True
    win.close()


def test_main_window_active_code_editor_delegation(app):
    win = MainWindow()

    win.tabs.setCurrentIndex(0)
    assert win.code_editor == win.py_editor

    win.tabs.setCurrentIndex(1)
    assert win.code_editor == win.arduino_editor
    win.close()


def test_main_window_load_project_with_uno_and_dual_codes(app):
    proj = ProjectModel(
        name="Projet Uno Dual Code",
        board_id="arduino_uno",
        language="arduino",
        files={
            "main.py": "print('Code Python')",
            "sketch.ino": "void setup() { Serial.println('Code Uno'); }"
        }
    )
    win = MainWindow()
    win._load_project(proj)

    # Vérifier que les codes sont chargés dans les bons éditeurs
    assert "Code Python" in win.py_editor.toPlainText()
    assert "Code Uno" in win.arduino_editor.toPlainText()

    # Vérifier l'état de l'interface Uno
    assert win.tabs.isTabEnabled(0) is False
    assert win.tabs.currentIndex() == 1
    win.close()


def test_main_window_simulation_runs_active_tab_code(app):
    win = MainWindow()
    win._switch_board("arduino_uno")
    win.arduino_editor.setPlainText("""
    void setup() {
        pinMode(13, OUTPUT);
        digitalWrite(13, HIGH);
    }
    void loop() {}
    """)

    win._start_simulation()
    deadline = time.time() + 1.0
    while time.time() < deadline:
        app.processEvents()
        time.sleep(0.02)
    win._stop_simulation()

    assert win.simulation_engine.gpio_manager.read(13) == 1
    win.close()


def test_main_window_quick_load_uno_example(app):
    win = MainWindow()
    win._load_example_by_key("uno_blink")

    assert win.current_project.board_id == "arduino_uno"
    assert win.tabs.currentIndex() == 1
    assert win.tabs.isTabEnabled(0) is False
    assert "LED_PIN = 13" in win.arduino_editor.toPlainText()

    # Rebasculer sur un exemple ESP32
    win._load_example_by_key("blink")
    assert win.current_project.board_id == "esp32_wroom_32"
    assert win.tabs.currentIndex() == 0
    assert win.tabs.isTabEnabled(0) is True
    assert "Pin(2" in win.py_editor.toPlainText()
    win.close()


def test_main_window_quick_load_uno_course_and_evaluate(app):
    win = MainWindow()
    win._load_course_by_id("uno_lesson_1_blink")

    assert win.current_project.board_id == "arduino_uno"
    assert win.tabs.currentIndex() == 1
    assert win.tabs.isTabEnabled(0) is False

    from esp32_lab.core.evaluator import ExerciseEvaluator
    evaluator = ExerciseEvaluator()
    res = evaluator.evaluate(win._current_lesson, win.current_project)
    assert res.passed is True
    assert res.score == 100
    win.close()


def test_examples_and_courses_dialog_filtering(app):
    from esp32_lab.ui.dialogs.examples_dialog import ExamplesDialog
    from esp32_lab.ui.dialogs.courses_dialog import CoursesDialog
    from esp32_lab.core.models.project import ProjectModel

    # 1. ExamplesDialog
    dlg_ex = ExamplesDialog()
    assert dlg_ex.list_widget.count() == len(dlg_ex.all_examples_meta)

    # Filtrer Uno
    dlg_ex.combo_filter.setCurrentIndex(1)
    assert dlg_ex.list_widget.count() == 6
    assert "Arduino Uno" in dlg_ex.badge_platform.text()

    # Filtrer ESP32
    dlg_ex.combo_filter.setCurrentIndex(2)
    assert dlg_ex.list_widget.count() == 16
    assert "ESP32" in dlg_ex.badge_platform.text()
    dlg_ex.close()

    # 2. CoursesDialog
    proj = ProjectModel(name="Test Proj", board_id="esp32_wroom_32")
    dlg_cr = CoursesDialog(proj)
    assert dlg_cr.list_widget.count() == len(dlg_cr.lessons)

    # Filtrer Uno TPs
    dlg_cr.combo_tp_filter.setCurrentIndex(1)
    assert dlg_cr.list_widget.count() == 6

    # Filtrer ESP32 TPs
    dlg_cr.combo_tp_filter.setCurrentIndex(2)
    assert dlg_cr.list_widget.count() == 11
    dlg_cr.close()
