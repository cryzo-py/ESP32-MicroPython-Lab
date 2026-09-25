"""
Tests d'intégration GUI pour MainWindow et l'interaction complète
"""

import time
from PySide6.QtWidgets import QApplication
import pytest

from esp32_lab.ui.main_window import MainWindow




def test_main_window_instantiation(app):
    window = MainWindow()
    assert window.windowTitle().startswith("ESP32 MicroPython Lab")
    assert window.code_editor is not None
    assert "main.py" in window.current_project.files
    assert window.circuit_scene is not None
    assert len(window.circuit_scene.component_items) > 0
    window.close()


def test_main_window_simulation_cycle(app):
    window = MainWindow()
    # Code test
    test_code = """
from machine import Pin
led = Pin(2, Pin.OUT)
led.value(1)
print("GUI_SIMULATION_SUCCESS")
"""
    window.code_editor.setPlainText(test_code)
    window._start_simulation()

    # Attendre l'exécution
    deadline = time.time() + 1.5
    while window.simulation_engine.is_running() and time.time() < deadline:
        app.processEvents()
        time.sleep(0.05)

    window._stop_simulation()
    
    # Vérifier que le statut visuel a bien détecté l'allumage
    assert "GUI_SIMULATION_SUCCESS" in window.console_panel.text_area.toPlainText()
    window.close()


def test_main_window_check_for_updates(app, monkeypatch):
    from PySide6.QtWidgets import QMessageBox
    # Empêcher l'ouverture de boîtes de dialogue bloquantes pendant le test
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)

    window = MainWindow()
    # Ne pas lancer de requête réseau réelle pendant le test
    monkeypatch.setattr("esp32_lab.core.updater.UpdateCheckerThread.start", lambda self: None)
    window._check_for_updates(manual=True)

    # Tester _on_update_finished sans mise à jour
    window._on_update_finished({"has_update": False, "current_version": "2.0"}, manual=True)

    # Tester _on_update_failed
    window._on_update_failed("Test error", manual=True)

    window.close()


def test_dirty_tracking_and_save_confirmation(app, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QMessageBox
    from PySide6.QtGui import QCloseEvent

    window = MainWindow()
    window._test_save_confirmation = True
    # État initial : non modifié
    assert not window.is_project_modified()
    assert window._maybe_save_changes() is True

    # 1. Modification du texte dans l'éditeur
    cursor = window.code_editor.textCursor()
    cursor.insertText("# modification test\n")
    assert window.is_project_modified() is True

    # 2. Test annulation (Annuler)
    prompt_shown = []
    def fake_exec_cancel(self):
        prompt_shown.append(True)
        cancel_btn = next(b for b in self.buttons() if self.buttonRole(b) == QMessageBox.RejectRole)
        self.clicked_button = cancel_btn
        return 0

    monkeypatch.setattr(QMessageBox, "exec", fake_exec_cancel)
    monkeypatch.setattr(QMessageBox, "clickedButton", lambda self: getattr(self, "clicked_button", None))

    assert window._maybe_save_changes("tester") is False
    assert len(prompt_shown) == 1

    # closeEvent doit être ignoré quand annulé
    close_event = QCloseEvent()
    window.closeEvent(close_event)
    assert not close_event.isAccepted()

    # 3. Test ne pas enregistrer (Discard)
    def fake_exec_discard(self):
        discard_btn = next(b for b in self.buttons() if self.buttonRole(b) == QMessageBox.DestructiveRole)
        self.clicked_button = discard_btn
        return 0

    monkeypatch.setattr(QMessageBox, "exec", fake_exec_discard)
    assert window._maybe_save_changes("tester") is True

    # 4. Test enregistrer (Save)
    save_target = tmp_path / "saved_test.lab32"
    window.current_file_path = save_target

    def fake_exec_save(self):
        save_btn = next(b for b in self.buttons() if self.buttonRole(b) == QMessageBox.AcceptRole)
        self.clicked_button = save_btn
        return 0

    monkeypatch.setattr(QMessageBox, "exec", fake_exec_save)
    assert window._maybe_save_changes("tester") is True
    assert save_target.exists()
    assert not window.is_project_modified()

    # Fermeture propre
    window.close()
