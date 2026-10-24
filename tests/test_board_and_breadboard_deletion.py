"""
Tests unitaires pour la suppression de la carte (ESP32 / Arduino Uno) et de la platine d'essai (Breadboard),
avec validation du cycle complet Undo / Redo et de l'intégrité topologique.
"""

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtGui import QUndoStack

from esp32_lab.ui.canvas.circuit_scene import CircuitScene
from esp32_lab.core.project_service import ProjectService
from esp32_lab.core.models.connection import ConnectionModel


def test_delete_esp32_board_first_time(app):
    """Vérifie que la carte ESP32 peut être supprimée dès la première fois sans avoir besoin d'insérer une deuxième carte."""
    scene = CircuitScene()
    scene.undo_stack = QUndoStack()
    project = ProjectService.create_default_project()
    scene.load_project_circuit(project)

    board = scene.board_item
    assert board is not None
    assert "esp32" in scene.component_items
    assert scene.board_item == board

    # Compter les connexions liées à l'esp32
    esp32_wires = [c for c in scene.connections if c.from_component == "esp32" or c.to_component == "esp32"]
    assert len(esp32_wires) > 0

    # Sélectionner la carte ESP32
    scene.clearSelection()
    board.setSelected(True)
    assert board in scene.selectedItems()

    # Supprimer la carte
    scene.delete_selected_items()

    # Vérifier que la carte est supprimée
    assert "esp32" not in scene.component_items
    assert scene.board_item is None
    # Vérifier que les fils vers l'ESP32 sont également supprimés
    remaining_esp_wires = [c for c in scene.connections if c.from_component == "esp32" or c.to_component == "esp32"]
    assert len(remaining_esp_wires) == 0

    # Tester l'annulation (Undo)
    scene.undo_stack.undo()
    assert "esp32" in scene.component_items
    assert scene.board_item is not None
    assert len([c for c in scene.connections if c.from_component == "esp32" or c.to_component == "esp32"]) == len(esp32_wires)

    # Tester le rétablissement (Redo)
    scene.undo_stack.redo()
    assert "esp32" not in scene.component_items
    assert scene.board_item is None


def test_delete_breadboard_first_time(app):
    """Vérifie que la plaque breadboard peut être supprimée dès la première fois avec ses composants et fils associés."""
    scene = CircuitScene()
    scene.undo_stack = QUndoStack()
    project = ProjectService.create_default_project()
    scene.load_project_circuit(project)

    bb = scene.breadboard_item
    assert bb is not None
    bb_id = bb.breadboard_id
    assert bb_id in scene.component_items

    # Des composants (LED, résistance) sont insérés sur cette breadboard
    led = scene.component_items.get("led_1")
    assert led is not None
    assert led.parentItem() == bb

    # Sélectionner la breadboard
    scene.clearSelection()
    bb.setSelected(True)
    assert bb in scene.selectedItems()

    # Supprimer la breadboard
    scene.delete_selected_items()

    # Vérifier que la breadboard et ses composants montés sont retirés de la scène
    assert scene.breadboard_item is None
    assert bb_id not in scene.component_items
    assert "led_1" not in scene.component_items

    # Annuler (Undo) : la breadboard et ses composants doivent être restaurés
    scene.undo_stack.undo()
    assert scene.breadboard_item is not None
    assert bb_id in scene.component_items
    assert "led_1" in scene.component_items
    restored_led = scene.component_items["led_1"]
    assert restored_led.parentItem() == scene.breadboard_item

    # Rétablir (Redo) : supprimés à nouveau
    scene.undo_stack.redo()
    assert scene.breadboard_item is None
    assert bb_id not in scene.component_items
    assert "led_1" not in scene.component_items


def test_add_board_and_breadboard_after_deletion(app):
    """Vérifie qu'après suppression, on peut rajouter une nouvelle carte ou breadboard depuis la palette."""
    scene = CircuitScene()
    project = ProjectService.create_default_project()
    scene.load_project_circuit(project)

    # Supprimer l'ESP32
    scene._execute_delete_items([scene.board_item])
    assert scene.board_item is None

    # Ajouter une nouvelle carte Arduino Uno
    new_uno = scene.add_component("arduino_uno")
    assert scene.board_item == new_uno
    assert "arduino_uno" in scene.component_items

    # Supprimer l'Uno
    scene._execute_delete_items([new_uno])
    assert scene.board_item is None

    # Rajouter un ESP32
    new_esp = scene.add_component("esp32")
    assert scene.board_item == new_esp
    assert "esp32" in scene.component_items


def test_delete_multiple_boards_scenario(app):
    """Vérifie le scénario où deux cartes sont insérées et supprimées individuellement ou ensemble."""
    scene = CircuitScene()
    scene.undo_stack = QUndoStack()
    project = ProjectService.create_default_project()
    scene.load_project_circuit(project)

    # Carte 1 initiale
    board1 = scene.board_item
    assert board1 is not None

    # Insérer une deuxième carte ESP32
    board2 = scene.add_component("esp32", QPointF(500, 100))
    assert board2 is not None
    assert board2.component_id == "esp32_1"
    assert "esp32_1" in scene.component_items

    # Sélectionner les deux cartes et les supprimer
    scene.clearSelection()
    board1.setSelected(True)
    board2.setSelected(True)
    assert len(scene.selectedItems()) == 2

    scene.delete_selected_items()
    assert "esp32" not in scene.component_items
    assert "esp32_1" not in scene.component_items
    assert scene.board_item is None

    # Annuler
    scene.undo_stack.undo()
    assert "esp32" in scene.component_items
    assert "esp32_1" in scene.component_items
    assert scene.board_item is not None


def test_circuit_view_delete_key_on_board_and_breadboard(app):
    """Vérifie que la touche Suppr (Delete) dans CircuitView supprime directement la carte ou la breadboard."""
    from PySide6.QtGui import QKeyEvent
    from PySide6.QtCore import Qt, QEvent
    from esp32_lab.ui.canvas.circuit_view import CircuitView

    scene = CircuitScene()
    scene.undo_stack = QUndoStack()
    view = CircuitView(scene)
    project = ProjectService.create_default_project()
    scene.load_project_circuit(project)

    board = scene.board_item
    assert board is not None

    # Sélectionner le board et envoyer l'événement touche Delete
    scene.clearSelection()
    board.setSelected(True)

    del_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
    view.keyPressEvent(del_event)

    assert "esp32" not in scene.component_items
    assert scene.board_item is None

    # Sélectionner la breadboard et envoyer l'événement touche Delete
    bb = scene.breadboard_item
    assert bb is not None
    scene.clearSelection()
    bb.setSelected(True)

    del_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Delete, Qt.NoModifier)
    view.keyPressEvent(del_event)

    assert scene.breadboard_item is None
    assert "breadboard_1" not in scene.component_items

