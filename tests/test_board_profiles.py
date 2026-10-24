"""
Tests unitaires pour le système de profils de cartes (Commit 1 — Board Profile System)
Vérifie le chargement des profils ESP32 et Arduino Uno, la gestion des broches,
l'intégration avec le ProjectModel, le GPIOManager et le SimulationEngine.
"""

import pytest

from esp32_lab.core.board_profiles import (
    load_board_profile,
    get_available_boards,
    BoardProfile,
    PinProfile,
    BoardPinType,
    DEFAULT_BOARD_ID,
)
from esp32_lab.core.models.project import ProjectModel, DEFAULT_MAIN_PY, DEFAULT_ARDUINO_INO
from esp32_lab.core.project_service import ProjectService
from esp32_lab.simulator.gpio import GPIOManager, GPIOMode, GPIOPull
from esp32_lab.simulator.engine import SimulationEngine


def test_load_esp32_profile():
    profile = load_board_profile("esp32_wroom_32")
    assert profile.id == "esp32_wroom_32"
    assert profile.mcu == "ESP-WROOM-32"
    assert profile.voltage == 3.3
    assert profile.adc_resolution == 4095
    assert profile.adc_bits == 12
    assert profile.built_in_led == 2
    assert "micropython" in profile.supported_languages
    assert "arduino_c" in profile.supported_languages
    assert profile.component_type == "esp32"

    # Vérification des broches spécifiques
    p2 = profile.get_pin(2)
    assert p2 is not None
    assert p2.pwm_supported is True
    assert p2.supports_output is True

    p34 = profile.get_pin(34)
    assert p34 is not None
    assert p34.input_only is True
    assert p34.supports_output is False


def test_load_arduino_uno_profile():
    profile = load_board_profile("arduino_uno")
    assert profile.id == "arduino_uno"
    assert profile.mcu == "ATmega328P"
    assert profile.voltage == 5.0
    assert profile.adc_resolution == 1023
    assert profile.adc_bits == 10
    assert profile.built_in_led == 13
    assert profile.pwm_max_duty == 255
    assert profile.pwm_frequency_default == 490
    assert "arduino_c" in profile.supported_languages
    assert profile.component_type == "arduino_uno"

    # Vérification des broches spécifiques Uno
    p13 = profile.get_pin(13)
    assert p13 is not None
    assert p13.name == "D13"

    p3 = profile.get_pin(3)
    assert p3 is not None
    assert p3.pwm_supported is True

    p4 = profile.get_pin(4)
    assert p4 is not None
    assert p4.pwm_supported is False

    pa0 = profile.get_pin("A0")
    assert pa0 is not None
    assert pa0.supports_adc is True


def test_get_available_boards():
    boards = get_available_boards()
    assert "esp32_wroom_32" in boards
    assert "arduino_uno" in boards


def test_board_profile_pin_lookups():
    uno = load_board_profile("arduino_uno")
    # Lookup par int
    assert uno.get_pin(13).name == "D13"
    # Lookup par str avec préfixe D
    assert uno.get_pin("D13").number == 13
    # Lookup par str analogique
    assert uno.get_pin("A4").supports_adc is True
    # Pin non existante
    assert uno.get_pin(99) is None

    assert uno.is_valid_pin(13) is True
    assert uno.is_valid_pin(99) is False
    assert uno.supports_pwm(3) is True
    assert uno.supports_pwm(4) is False
    assert uno.supports_adc("A0") is True


def test_project_model_language_and_board_fields():
    # Projet standard
    p = ProjectModel()
    assert p.board_id == "esp32_wroom_32"
    assert p.language == "micropython"
    assert "main.py" in p.files

    # Sérialisation / Désérialisation
    p_dict = p.to_dict()
    assert p_dict["board_id"] == "esp32_wroom_32"
    assert p_dict["language"] == "micropython"

    p_restored = ProjectModel.from_dict(p_dict)
    assert p_restored.board_id == "esp32_wroom_32"
    assert p_restored.language == "micropython"

    # Projet Arduino Uno
    p_uno = ProjectModel(
        name="Projet Uno",
        board_id="arduino_uno",
        language="arduino_c",
        files={"sketch.ino": DEFAULT_ARDUINO_INO}
    )
    assert p_uno.get_main_code() == DEFAULT_ARDUINO_INO
    p_uno.set_main_code("// Nouveau code C")
    assert p_uno.get_main_code() == "// Nouveau code C"

    uno_dict = p_uno.to_dict()
    assert uno_dict["board_id"] == "arduino_uno"
    assert uno_dict["language"] == "arduino_c"

    uno_restored = ProjectModel.from_dict(uno_dict)
    assert uno_restored.board_id == "arduino_uno"
    assert uno_restored.language == "arduino_c"
    assert uno_restored.get_main_code() == "// Nouveau code C"


def test_project_service_create_empty_project_with_options():
    p_py = ProjectService.create_empty_project("TP Python", board_id="esp32_wroom_32", language="micropython")
    assert p_py.language == "micropython"
    assert "main.py" in p_py.files

    p_c = ProjectService.create_empty_project("TP Arduino Uno", board_id="arduino_uno", language="arduino_c")
    assert p_c.board_id == "arduino_uno"
    assert p_c.language == "arduino_c"
    assert "sketch.ino" in p_c.files
    assert p_c.get_main_code() == ""


def test_gpio_manager_with_uno_profile():
    uno = load_board_profile("arduino_uno")
    mgr = GPIOManager(board_profile=uno)

    # Broche valide Uno (ex: 13)
    mgr.configure(13, GPIOMode.OUT)
    mgr.write(13, 1)
    assert mgr.read(13) == 1
    mgr.write(13, 0)
    assert mgr.read(13) == 0

    # Broche inexistante sur Uno (ex: GPIO 34 d'un ESP32)
    with pytest.raises(ValueError, match="invalide"):
        mgr.configure(34, GPIOMode.IN)

    # Résolution ADC clampée à 1023 sur Uno
    mgr.set_adc_value(14, 5000)
    assert mgr.read_adc(14) == 1023

    mgr.set_adc_value(14, 512)
    assert mgr.read_adc(14) == 512


def test_gpio_manager_with_esp32_profile():
    esp = load_board_profile("esp32_wroom_32")
    mgr = GPIOManager(board_profile=esp)

    # Broche 34 valide en entrée sur ESP32
    mgr.configure(34, GPIOMode.IN)

    # Broche 34 interdite en sortie sur ESP32 (input only)
    with pytest.raises(ValueError, match="input-only"):
        mgr.configure(34, GPIOMode.OUT)

    # Résolution ADC clampée à 4095 sur ESP32
    mgr.set_adc_value(32, 5000)
    assert mgr.read_adc(32) == 4095


def test_simulation_engine_board_profile_switching(app):
    engine = SimulationEngine()
    # Par défaut, profil ESP32
    assert engine.gpio_manager.board_profile.id == "esp32_wroom_32"
    assert engine.adc_manager.board.adc_resolution == 4095

    # Basculement vers Arduino Uno
    uno = load_board_profile("arduino_uno")
    engine.set_board_profile(uno)

    assert engine.gpio_manager.board_profile.id == "arduino_uno"
    assert engine.adc_manager.board.adc_resolution == 1023
    assert engine.pwm_manager.board.pwm_max_duty == 255
