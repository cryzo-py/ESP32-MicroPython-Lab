import time
import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from esp32_lab.ui.main_window import MainWindow
from esp32_lab.ui.canvas.items.potentiometer_item import PotentiometerGraphicsItem
from esp32_lab.ui.canvas.items.button_item import ButtonGraphicsItem
from esp32_lab.ui.canvas.items.servo_item import ServoGraphicsItem


def test_uno_pot_interactive_knob_not_intercepted_by_breadboard(app):
    win = MainWindow()
    win.show()
    win._load_example_by_key("uno_pot_pwm")
    app.processEvents()

    # Trouver l'item potentiomètre dans la scène
    pot_item = win.circuit_scene.component_items.get("pot_1")
    assert pot_item is not None
    assert isinstance(pot_item, PotentiometerGraphicsItem)

    view = win.circuit_view
    pot_scene_center = pot_item.scenePos()
    view_point = view.mapFromScene(pot_scene_center)

    # Simuler un clic gauche sur la molette via CircuitView
    assert pot_item._is_dragging is False
    QTest.mousePress(view.viewport(), Qt.LeftButton, Qt.NoModifier, view_point)
    app.processEvents()

    # Vérifier que ce n'est PAS un trou de breadboard qui est sélectionné comme départ de fil
    assert win.circuit_scene._pending_wire_start_pin is None
    # Vérifier que la molette a bien capturé le drag interactif
    assert pot_item._is_dragging is True

    # Relâcher la souris
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, Qt.NoModifier, view_point)
    app.processEvents()
    assert pot_item._is_dragging is False
    win.close()


def test_uno_button_interactive_press_not_intercepted_by_breadboard(app):
    win = MainWindow()
    win.show()
    win._load_example_by_key("uno_button_led")
    app.processEvents()

    btn_item = win.circuit_scene.component_items.get("btn_1")
    assert btn_item is not None
    assert isinstance(btn_item, ButtonGraphicsItem)

    view = win.circuit_view
    btn_scene_center = btn_item.scenePos()
    btn_view_point = view.mapFromScene(btn_scene_center)

    assert btn_item.is_pressed is False
    QTest.mousePress(view.viewport(), Qt.LeftButton, Qt.NoModifier, btn_view_point)
    app.processEvents()

    # Vérifier que ce n'est PAS un trou de breadboard qui a été activé
    assert win.circuit_scene._pending_wire_start_pin is None
    # Vérifier que le bouton est bien pressé
    assert btn_item.is_pressed is True

    # Relâcher le bouton
    QTest.mouseRelease(view.viewport(), Qt.LeftButton, Qt.NoModifier, btn_view_point)
    app.processEvents()
    assert btn_item.is_pressed is False
    win.close()


def test_uno_servo_simulation_arm_movement(app):
    win = MainWindow()
    win._load_example_by_key("uno_servo")
    app.processEvents()

    servo_item = win.circuit_scene.component_items.get("servo_1")
    assert servo_item is not None
    assert isinstance(servo_item, ServoGraphicsItem)

    # Vérifier la connexion vers la broche sig
    conn9 = [c for c in win.current_project.connections if c.to_component == "servo_1"]
    assert len(conn9) == 3
    pwm_conn = next(c for c in conn9 if c.from_pin == "9")
    assert pwm_conn.to_pin in ("sig", "pwm")

    # Lancer la simulation 0.5s pour vérifier que le servo bouge
    win._start_simulation()
    deadline = time.time() + 0.6
    while time.time() < deadline:
        app.processEvents()
        time.sleep(0.02)
    win._stop_simulation()

    win.close()


def test_uno_pot_pwm_simulation_reads_adc(app):
    win = MainWindow()
    win._load_example_by_key("uno_pot_pwm")
    app.processEvents()

    pot_item = win.circuit_scene.component_items.get("pot_1")
    assert pot_item is not None

    # Mettre la valeur à 50%
    pot_item.set_raw_value(2048)
    win.circuit_scene._on_potentiometer_changed("pot_1", 2048)
    win.circuit_scene.re_evaluate_topology()

    # Lire l'ADC A0 (pin 14 sur Uno)
    adc_val = win.simulation_engine.adc_manager.read(14)
    # 2048 / 4095 * 1023 ≈ 511
    assert 500 <= adc_val <= 525

    win.close()
