"""
Tests pour la bascule de thèmes (Sombre / Clair) et la persistance des préférences.
"""

import pytest
from PySide6.QtCore import QSettings
from esp32_lab.app.theme import apply_theme, DARK_THEME_QSS, LIGHT_THEME_QSS
from esp32_lab.ui.main_window import MainWindow
from esp32_lab.ui.canvas.circuit_scene import CircuitScene
from esp32_lab.ui.canvas.schematic_scene import SchematicScene


def test_theme_functions(app):
    """Vérifie que les fonctions apply_theme fonctionnent sans erreur."""
    apply_theme(app, "dark")
    assert app.styleSheet() == DARK_THEME_QSS

    apply_theme(app, "light")
    assert app.styleSheet() == LIGHT_THEME_QSS

    apply_theme(app, "dark")
    assert app.styleSheet() == DARK_THEME_QSS


def test_scene_theme_updates(app):
    """Vérifie l'ajustement du fond des scènes 2D lors du changement de thème."""
    circuit = CircuitScene()
    schematic = SchematicScene()

    # Thème sombre
    circuit.set_theme("dark")
    schematic.set_theme("dark")
    assert circuit.theme_name == "dark"
    assert schematic.theme_name == "dark"

    # Thème clair
    circuit.set_theme("light")
    schematic.set_theme("light")
    assert circuit.theme_name == "light"
    assert schematic.theme_name == "light"


def test_main_window_theme_switching(app):
    """Vérifie le sélecteur de thème dans MainWindow et les actions de menu."""
    window = MainWindow()
    
    # Bascule vers Light
    window._set_app_theme("light")
    assert window.act_theme_light.isChecked()
    assert not window.act_theme_dark.isChecked()
    assert window.circuit_scene.theme_name == "light"
    assert window.schematic_scene.theme_name == "light"

    settings = QSettings("ESP32Lab", "ESP32MicroPythonLab")
    assert settings.value("theme") == "light"

    # Rebascule vers Dark
    window._set_app_theme("dark")
    assert window.act_theme_dark.isChecked()
    assert not window.act_theme_light.isChecked()
    assert window.circuit_scene.theme_name == "dark"
    assert settings.value("theme") == "dark"

    window.close()
