"""
Configuration partagée des tests pytest pour ESP32 MicroPython Lab
Assure qu'une unique instance QApplication (offscreen/GUI) est créée pour la session de test.
"""

import os
import sys
import pytest
from PySide6.QtWidgets import QApplication

# Définir la plateforme offscreen pour l'exécution sans affichage graphique obligatoire
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session", autouse=True)
def app():
    instance = QApplication.instance()
    if instance is None:
        instance = QApplication(["pytest", "-platform", "offscreen"])
    return instance


@pytest.fixture(autouse=True)
def reset_globals():
    """Réinitialise l'EventBus global et les singletons statiques avant chaque test."""
    try:
        from esp32_lab.app.event_bus import reset_event_bus
        reset_event_bus()
    except ImportError:
        pass
    try:
        from esp32_lab.simulator.modules import machine as sim_machine
        sim_machine.Pin._gpio_manager = None
        sim_machine.Pin._irq_controller = None
    except ImportError:
        pass
