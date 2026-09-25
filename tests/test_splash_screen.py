"""
Tests unitaires pour l'écran de démarrage (SplashScreen)
"""

import pytest
from PySide6.QtWidgets import QApplication

from esp32_lab.ui.splash_screen import SplashScreen


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_splash_screen_creation(qapp):
    """Vérifie la création, les composants et la taille du SplashScreen."""
    splash = SplashScreen()
    assert splash is not None
    assert splash.progress_bar is not None
    assert splash.status_label is not None
    assert splash.title_label is not None
    assert splash.logo_label is not None

    # Barre de progression initialement à 0
    assert splash.progress_bar.value() == 0
    splash.close()


def test_splash_screen_set_progress(qapp):
    """Vérifie la mise à jour manuelle de la progression et du statut."""
    splash = SplashScreen()
    splash.set_progress(45, "Chargement des modules...")
    assert splash.progress_bar.value() == 45
    assert splash.status_label.text() == "Chargement des modules..."

    # Test des limites (0-100)
    splash.set_progress(150, "Au-delà")
    assert splash.progress_bar.value() == 100

    splash.set_progress(-20, "En-dessous")
    assert splash.progress_bar.value() == 0
    splash.close()


def test_splash_screen_finish_signal(qapp):
    """Vérifie l'émission du signal de fin de chargement."""
    splash = SplashScreen()
    finished = []
    splash.loading_finished.connect(lambda: finished.append(True))

    splash._finish_loading()
    assert len(finished) == 1
    splash.close()
