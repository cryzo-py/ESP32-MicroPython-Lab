"""
Tests pour les modules IoT (Network, NeoPixel), l'actionneur Relais,
la persistance SQLite et les nouvelles leçons du cursus.
"""

import pytest
import os
import tempfile
from esp32_lab.simulator.modules.neopixel import NeoPixel, add_neopixel_listener, remove_neopixel_listener
from esp32_lab.simulator.modules import network
from esp32_lab.core.database import ProgressDatabase
from esp32_lab.core.courses import get_course_curriculum
from esp32_lab.core.evaluator import ExerciseEvaluator
from esp32_lab.ui.canvas.items.relay_item import RelayGraphicsItem
from esp32_lab.ui.canvas.items.neopixel_item import NeoPixelGraphicsItem


def test_neopixel_module():
    """Vérifie le fonctionnement du module simulé neopixel."""
    received = []
    def on_update(pin, colors):
        received.append((pin, colors))

    add_neopixel_listener(on_update)
    
    np = NeoPixel(5, 8)
    assert len(np) == 8
    assert np[0] == (0, 0, 0)

    # Assigner une LED
    np[0] = (255, 0, 128)
    assert np[0] == (255, 0, 128)

    # Remplir tout l'anneau
    np.fill((10, 20, 30))
    for i in range(8):
        assert np[i] == (10, 20, 30)

    # Déclencher write()
    np.write()
    assert len(received) >= 1
    assert received[-1][0] == 5
    assert len(received[-1][1]) == 8
    assert received[-1][1][0] == (10, 20, 30)

    remove_neopixel_listener(on_update)


def test_network_module():
    """Vérifie le fonctionnement du module simulé network et de la classe WLAN."""
    wlan = network.WLAN(network.STA_IF)
    assert not wlan.active()
    assert not wlan.isconnected()

    wlan.active(True)
    assert wlan.active()

    # Scan des réseaux
    nets = wlan.scan()
    assert len(nets) >= 1
    assert nets[0][0] == b"ESP32_Lab_WiFi"

    # Connexion
    wlan.connect("ESP32_Lab_WiFi", "password123")
    assert wlan.isconnected()

    # Configuration IP
    ip_cfg = wlan.ifconfig()
    assert len(ip_cfg) == 4
    # L'IP peut être simulée (192.168.x.x) ou réelle (Host Bridge), on vérifie juste le format basique
    assert isinstance(ip_cfg[0], str) and ip_cfg[0].count(".") == 3


def test_progress_database():
    """Vérifie la création de la base de données SQLite et la persistance des résultats de TP."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_progress.db")
        db = ProgressDatabase(db_path)

        # Vérifier état initial
        assert db.get_completed_lessons() == set()

        # Créer une leçon factice
        curriculum = get_course_curriculum()
        lesson_1 = curriculum[0]
        evaluator = ExerciseEvaluator()

        result = evaluator.evaluate(lesson_1, lesson_1.starter_project)
        assert result.passed

        # Enregistrer l'évaluation
        db.record_evaluation(result, lesson_1.starter_project.get_main_code())

        completed = db.get_completed_lessons()
        assert lesson_1.id in completed

        stats = db.get_summary_stats()
        assert stats["passed_lessons"] >= 1
        assert stats["average_score"] >= 70


def test_relay_graphics_item():
    """Vérifie les états et les bornes du composant graphique Relais 5V."""
    relay = RelayGraphicsItem("relay_1")
    assert not relay.is_active

    # Passer le relais à l'état actif
    relay.set_state(True)
    assert relay.is_active

    # Revenir au repos
    relay.set_state(False)
    assert not relay.is_active

    # Vérifier la présence des broches NO, COM, NC, VCC, GND, IN
    anchors = relay.get_anchor_pins()
    pin_ids = [a.pin_id for a in anchors]
    assert "no" in pin_ids
    assert "com" in pin_ids
    assert "nc" in pin_ids
    assert "vcc" in pin_ids
    assert "gnd" in pin_ids
    assert "in" in pin_ids


def test_neopixel_graphics_item():
    """Vérifie le composant visuel de l'anneau NeoPixel."""
    ring = NeoPixelGraphicsItem("np_1", num_leds=8)
    assert ring.num_leds == 8
    assert len(ring.led_colors) == 8

    # Mettre à jour les couleurs
    test_colors = [(255, 0, 0)] * 8
    ring.set_colors(test_colors)
    assert ring.led_colors[0] == (255, 0, 0)

    # Éteindre
    ring.clear()
    assert ring.led_colors[0] == (0, 0, 0)


def test_new_course_lessons():
    """Vérifie que les TPs 9, 10, 11 sont bien présents et s'évaluent avec succès."""
    curriculum = get_course_curriculum()
    lesson_ids = [l.id for l in curriculum]

    assert "lesson_9_relay" in lesson_ids
    assert "lesson_10_neopixel" in lesson_ids
    assert "lesson_11_wifi" in lesson_ids

    evaluator = ExerciseEvaluator()

    for target_id in ("lesson_9_relay", "lesson_10_neopixel", "lesson_11_wifi"):
        lesson = next(l for l in curriculum if l.id == target_id)
        assert lesson.starter_project is not None
        result = evaluator.evaluate(lesson, lesson.starter_project)
        assert result.passed, f"La leçon {target_id} a échoué à l'évaluation : {result.general_feedback}"
        assert result.score >= 70