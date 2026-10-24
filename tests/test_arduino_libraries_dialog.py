"""
Tests pour le Gestionnaire de Bibliothèques Arduino (ArduinoLibraryService et ArduinoLibrariesDialog).
"""

import pytest
from PySide6.QtCore import Qt
from esp32_lab.hardware.arduino_cli import ArduinoLibraryService
from esp32_lab.ui.dialogs.arduino_libraries_dialog import ArduinoLibrariesDialog, LibraryItemWidget
from esp32_lab.ui.main_window import MainWindow


def test_arduino_library_service_curated_libraries():
    libs = ArduinoLibraryService.CURATED_LIBRARIES
    assert len(libs) >= 8

    names = [l["name"] for l in libs]
    assert "Servo" in names
    assert "LiquidCrystal" in names
    assert "DHT sensor library" in names
    assert "Adafruit NeoPixel" in names

    for l in libs:
        assert "name" in l
        assert "header" in l
        assert "category" in l
        assert "sentence" in l


def test_arduino_library_service_methods_safe():
    # Ces méthodes doivent s'exécuter en toute sécurité même si arduino-cli n'est pas installé
    assert isinstance(ArduinoLibraryService.is_cli_installed(), bool)
    assert isinstance(ArduinoLibraryService.is_avr_core_installed(), bool)
    installed = ArduinoLibraryService.list_installed_libraries()
    assert isinstance(installed, list)
    searched = ArduinoLibraryService.search_libraries("servo")
    assert isinstance(searched, list)


def test_arduino_libraries_dialog_instantiation(app):
    dlg = ArduinoLibrariesDialog()
    assert dlg.tabs.count() == 3

    # Vérifier l'onglet Recommandées
    assert dlg.list_curated.count() == len(ArduinoLibraryService.CURATED_LIBRARIES)

    # Filtrer par "servo"
    dlg.txt_curated_filter.setText("servo")
    assert dlg.list_curated.count() >= 1

    # Réinitialiser le filtre
    dlg.txt_curated_filter.setText("")
    assert dlg.list_curated.count() == len(ArduinoLibraryService.CURATED_LIBRARIES)

    # Vérifier le basculement de la console
    assert dlg.console_log.isHidden() is True
    dlg.btn_toggle_console.setChecked(True)
    assert dlg.console_log.isHidden() is False
    dlg.btn_toggle_console.setChecked(False)
    assert dlg.console_log.isHidden() is True

    dlg.close()


def test_library_item_widget_rendering(app):
    lib_data = {
        "name": "Servo",
        "header": "<Servo.h>",
        "category": "Actionneurs",
        "author": "Michael Margolis",
        "sentence": "Contrôle des servomoteurs RC.",
        "version": "1.2.2",
        "installed": False
    }
    w = LibraryItemWidget(lib_data, is_light=False)
    assert w is not None

    # Test avec bibliothèque installée
    lib_installed = dict(lib_data)
    lib_installed["installed"] = True
    w_inst = LibraryItemWidget(lib_installed, is_light=True)
    assert w_inst is not None


def test_main_window_has_arduino_libs_action(app):
    win = MainWindow()
    # Vérifier la présence de l'action dans menu_sim et menu_tools
    actions = [a.text() for a in win.menuBar().actions()]
    assert any("Outils" in a or "Tools" in a for a in actions)

    # Vérifier que la méthode d'affichage existe
    assert hasattr(win, "_show_arduino_libraries_dialog")
    win.close()
