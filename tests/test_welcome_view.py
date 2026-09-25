"""
Tests unitaires pour la page d'accueil (WelcomeWidget), les miniatures de la palette et l'intégration dans MainWindow.
"""

from pathlib import Path
import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication

from esp32_lab.ui.main_window import MainWindow
from esp32_lab.ui.panels.welcome_view import ActionCard, WelcomeWidget
from esp32_lab.ui.panels.component_palette import render_component_thumbnail


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_welcome_widget_creation(qapp):
    widget = WelcomeWidget()
    assert widget is not None
    assert widget.chk_startup is not None
    assert widget.recent_list is not None


def test_welcome_widget_signals(qapp):
    widget = WelcomeWidget()
    new_proj_fired = []
    open_proj_fired = []
    examples_fired = []
    courses_fired = []
    workspace_fired = []

    widget.new_project_requested.connect(lambda: new_proj_fired.append(True))
    widget.open_project_requested.connect(lambda: open_proj_fired.append(True))
    widget.examples_requested.connect(lambda: examples_fired.append(True))
    widget.courses_requested.connect(lambda: courses_fired.append(True))
    widget.workspace_requested.connect(lambda: workspace_fired.append(True))

    widget.new_project_requested.emit()
    assert len(new_proj_fired) == 1

    widget.open_project_requested.emit()
    assert len(open_proj_fired) == 1

    widget.examples_requested.emit()
    assert len(examples_fired) == 1

    widget.courses_requested.emit()
    assert len(courses_fired) == 1

    widget.workspace_requested.emit()
    assert len(workspace_fired) == 1


def test_welcome_recent_files_refresh(qapp, tmp_path):
    settings = QSettings("ESP32Lab", "ESP32MicroPythonLab")
    test_file = str(tmp_path / "test_demo.esp32lab")
    settings.setValue("recent_files", [test_file])

    widget = WelcomeWidget()
    widget.refresh_recent_files()

    assert widget.recent_list.count() == 1
    item = widget.recent_list.item(0)
    assert item.data(Qt.UserRole) == test_file


def test_main_window_stacked_navigation(qapp):
    settings = QSettings("ESP32Lab", "ESP32MicroPythonLab")
    settings.setValue("show_welcome_on_startup", True)

    win = MainWindow()
    # Par défaut avec show_welcome_on_startup=True, la page d'accueil (index 0) doit être affichée
    assert win.central_stack.currentIndex() == 0

    # Navigation vers le laboratoire
    win._show_workspace_view()
    assert win.central_stack.currentIndex() == 1

    # Navigation retour vers l'accueil
    win._show_welcome_view()
    assert win.central_stack.currentIndex() == 0

    # Test clic bouton accueil dans le header
    win.btn_nav_lab.click()
    assert win.central_stack.currentIndex() == 1

    win.btn_nav_home.click()
    assert win.central_stack.currentIndex() == 0

    win.close()


def test_component_thumbnails_generation(qapp):
    components = ["led", "resistor", "esp32", "breadboard", "button", "potentiometer", "dht22", "oled", "relay", "servo", "buzzer", "neopixel", "ultrasonic"]
    for comp in components:
        pix = render_component_thumbnail(comp, 44)
        assert pix is not None
        assert not pix.isNull()
        assert pix.width() == 44
        assert pix.height() == 44
