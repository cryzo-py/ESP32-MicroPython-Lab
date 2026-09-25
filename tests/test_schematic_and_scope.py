"""
Tests pour la vue schématique CEI/IEEE, l'oscilloscope virtuel et le générateur de rapports de TP.
"""

import tempfile
from pathlib import Path
import pytest
from PySide6.QtCore import QPointF

from esp32_lab.core.courses import get_course_curriculum
from esp32_lab.core.evaluator import ExerciseEvaluator
from esp32_lab.core.examples import create_blink_example, create_pot_pwm_example
from esp32_lab.core.report_generator import LabReportGenerator
from esp32_lab.ui.canvas.schematic_scene import ESP32SchematicItem, SchematicScene, SchematicSymbolItem
from esp32_lab.ui.main_window import MainWindow
from esp32_lab.ui.panels.oscilloscope_panel import OscilloscopePanel, OscilloscopeScreen


def test_schematic_scene():
    """Vérifie la génération du schéma électrique normalisé."""
    scene = SchematicScene()
    proj = create_blink_example()
    scene.load_project_schematic(proj)

    # Vérifier la présence du bloc ESP32
    assert "esp32" in scene.symbols
    esp_item = scene.symbols["esp32"]
    assert isinstance(esp_item, ESP32SchematicItem)

    # Vérifier la position d'une broche ESP32
    p_gnd = esp_item.get_pin_scene_pos("GND_1")
    assert isinstance(p_gnd, QPointF)

    # Vérifier la présence des composants
    assert len(scene.symbols) >= 3  # esp32 + led + resistor
    assert len(scene.wires) >= 1

    # Mettre à jour les fils
    scene.update_wires()


def test_oscilloscope_panel():
    """Vérifie le fonctionnement de l'oscilloscope virtuel et de l'analyseur logique."""
    panel = OscilloscopePanel()
    screen = panel.screen

    assert screen.is_running
    assert len(screen.ch1_samples) == 0
    assert len(screen.ch2_samples) == 0

    # Ajouter des échantillons numériques sur voie 1
    screen.add_ch1_sample(1)
    screen.add_ch1_sample(0)
    assert len(screen.ch1_samples) == 2

    # Ajouter des échantillons analogiques sur voie 2
    screen.add_ch2_sample(2.5)
    assert len(screen.ch2_samples) == 1
    assert screen.latest_voltage == 2.5

    # Test Hold / Run
    panel._toggle_run()
    assert not screen.is_running
    panel._toggle_run()
    assert screen.is_running

    # Test Base de temps
    panel._on_timebase_changed(0)
    assert screen.timebase_sec == 0.5

    # Effacer
    panel._clear_screen()
    assert len(screen.ch1_samples) == 0


def test_lab_report_generator():
    """Vérifie la génération d'un compte-rendu HTML de TP."""
    curriculum = get_course_curriculum()
    lesson = curriculum[0]
    proj = lesson.starter_project
    evaluator = ExerciseEvaluator()
    result = evaluator.evaluate(lesson, proj)

    generator = LabReportGenerator()
    html = generator.generate_html(lesson, proj, result, student_name="Alice Martin")

    assert "ESP32 MicroPython Lab" in html
    assert "Alice Martin" in html
    assert lesson.title in html
    assert str(result.score) in html
    assert "Bill of Materials" in html
    assert "main.py" in html

    # Sauvegarde sur disque
    with tempfile.TemporaryDirectory() as tmpdir:
        report_file = Path(tmpdir) / "test_report.html"
        generator.save_report(report_file, lesson, proj, result, student_name="Alice Martin")
        assert report_file.exists()
        assert report_file.stat().st_size > 1000


def test_main_window_schematic_switch():
    """Vérifie la bascule entre vue maquette réaliste et vue schématique dans la fenêtre principale."""
    win = MainWindow()
    assert win.circuit_view.scene() == win.circuit_scene

    # Basculer vers vue schématique
    win._show_schematic_view()
    assert win.circuit_view.scene() == win.schematic_scene
    assert win.status_overlay.isHidden()

    # Revenir vers vue simulation
    win._show_simulation_view()
    assert win.circuit_view.scene() == win.circuit_scene
    assert not win.status_overlay.isHidden()

    win.close()