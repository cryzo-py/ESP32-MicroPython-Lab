"""Tests de non-régression pour l'interaction avec les trous de breadboard et les embouts de fils."""
import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QApplication

from esp32_lab.core.models.project import ConnectionModel
from esp32_lab.core.project_service import ProjectService
from esp32_lab.ui.main_window import MainWindow


def test_click_adjacent_hole_selects_hole_and_does_not_move_wire(app):
    """Vérifie que cliquer sur le trou à côté d'un fil sélectionne ce trou et ne déplace PAS le fil."""
    window = MainWindow()
    project = ProjectService.create_default_project()
    window._load_project(project)
    
    scene = window.circuit_view.circuit_scene
    bb = scene.breadboard_item
    view = window.circuit_view
    
    # Trouver le fil connecté à r10_a
    conn = next((c for c in scene.connections if c.to_pin == "r10_a"), None)
    assert conn is not None
    assert conn.to_pin == "r10_a"
    
    # Coordonnées du trou r10_c (trou libre adjacent dans la même rangée 10)
    hole_c = bb.get_pin_anchor("r10_c")
    assert hole_c is not None
    assert hole_c.is_occupied is False
    scene_pos_c = hole_c.scenePos()
    view_pos_c = view.mapFromScene(scene_pos_c)
    
    # 1. Simuler un clic de souris sur le trou libre r10_c
    press_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(view_pos_c),
        scene_pos_c,
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    view.mousePressEvent(press_event)
    
    # Vérifier que le trou r10_c a bien été sélectionné comme point de départ de fil
    assert scene._pending_wire_start_pin is not None
    assert scene._pending_wire_start_pin.pin_id == "r10_c"
    assert hole_c._is_active is True
    
    # 2. Relâcher le clic sur r10_c
    release_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        QPointF(view_pos_c),
        scene_pos_c,
        Qt.LeftButton,
        Qt.NoButton,
        Qt.NoModifier,
    )
    view.mouseReleaseEvent(release_event)
    
    # Vérifier que le fil n'a ABSOLUMENT PAS été déplacé vers r10_c !
    assert conn.to_pin == "r10_a"
    
    window.close()


def test_click_without_drag_on_wire_terminal_does_not_move_it(app):
    """Vérifie qu'un simple clic sans glissement sur l'embout d'un fil ne le déplace pas."""
    window = MainWindow()
    project = ProjectService.create_default_project()
    window._load_project(project)
    
    scene = window.circuit_view.circuit_scene
    bb = scene.breadboard_item
    view = window.circuit_view
    
    conn = next((c for c in scene.connections if c.to_pin == "r10_a"), None)
    assert conn is not None
    
    hole_a = bb.get_pin_anchor("r10_a")
    scene_pos_a = hole_a.scenePos()
    view_pos_a = view.mapFromScene(scene_pos_a)
    
    # Clic sur r10_a (où se trouve le fil)
    press_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(view_pos_a),
        scene_pos_a,
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    view.mousePressEvent(press_event)
    
    # Relâchement immédiat au même endroit sans bouger la souris
    release_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        QPointF(view_pos_a),
        scene_pos_a,
        Qt.LeftButton,
        Qt.NoButton,
        Qt.NoModifier,
    )
    view.mouseReleaseEvent(release_event)
    
    # Le fil doit rester sur r10_a
    assert conn.to_pin == "r10_a"
    
    window.close()


def test_click_hole_above_selects_hole_and_does_not_move_wire(app):
    """Vérifie que cliquer sur le trou de la ligne au-dessus (r9_a) sélectionne ce trou et ne déplace pas le fil de r10_a."""
    window = MainWindow()
    project = ProjectService.create_default_project()
    window._load_project(project)
    
    scene = window.circuit_view.circuit_scene
    bb = scene.breadboard_item
    view = window.circuit_view
    
    conn = next((c for c in scene.connections if c.to_pin == "r10_a"), None)
    assert conn is not None
    
    hole_9a = bb.get_pin_anchor("r9_a")
    assert hole_9a is not None
    assert hole_9a.is_occupied is False
    scene_pos_9a = hole_9a.scenePos()
    view_pos_9a = view.mapFromScene(scene_pos_9a)
    
    # Clic sur r9_a
    press_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(view_pos_9a),
        scene_pos_9a,
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    view.mousePressEvent(press_event)
    
    assert scene._pending_wire_start_pin is not None
    assert scene._pending_wire_start_pin.pin_id == "r9_a"
    
    release_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        QPointF(view_pos_9a),
        scene_pos_9a,
        Qt.LeftButton,
        Qt.NoButton,
        Qt.NoModifier,
    )
    view.mouseReleaseEvent(release_event)
    
    assert conn.to_pin == "r10_a"
    window.close()


def test_drag_wire_terminal_reconnects_when_genuinely_dragged(app):
    """Vérifie que glisser-déposer délibérément l'embout d'un fil le reconnecte au trou cible."""
    window = MainWindow()
    project = ProjectService.create_default_project()
    window._load_project(project)
    
    scene = window.circuit_view.circuit_scene
    bb = scene.breadboard_item
    view = window.circuit_view
    
    conn = next((c for c in scene.connections if c.to_pin == "r10_a"), None)
    assert conn is not None
    
    hole_10a = bb.get_pin_anchor("r10_a")
    hole_15a = bb.get_pin_anchor("r15_a")
    scene_pos_10a = hole_10a.scenePos()
    scene_pos_15a = hole_15a.scenePos()
    view_pos_10a = view.mapFromScene(scene_pos_10a)
    view_pos_15a = view.mapFromScene(scene_pos_15a)
    
    # 1. Press sur r10_a
    press_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(view_pos_10a),
        scene_pos_10a,
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    view.mousePressEvent(press_event)
    
    # 2. Move vers r15_a (glissement délibéré)
    move_event = QMouseEvent(
        QMouseEvent.Type.MouseMove,
        QPointF(view_pos_15a),
        scene_pos_15a,
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    view.mouseMoveEvent(move_event)
    
    # 3. Release sur r15_a
    release_event = QMouseEvent(
        QMouseEvent.Type.MouseButtonRelease,
        QPointF(view_pos_15a),
        scene_pos_15a,
        Qt.LeftButton,
        Qt.NoButton,
        Qt.NoModifier,
    )
    view.mouseReleaseEvent(release_event)
    
    # Le fil doit être reconnecté à r15_a
    assert conn.to_pin == "r15_a"
    window.close()


def test_direct_wire_connection_to_free_components_without_breadboard(app):
    """Vérifie qu'on peut brancher des fils directement entre des composants (LED, Switch, LDR) sans platine."""
    window = MainWindow()
    # Créer un projet vierge sans breadboard ou avec composants libres
    empty_proj = ProjectService.create_empty_project()
    window._load_project(empty_proj)
    
    scene = window.circuit_view.circuit_scene
    view = window.circuit_view
    
    # Ajouter une LED, un Switch et un LDR
    led = scene.add_component("led", QPointF(100, 100))
    switch = scene.add_component("switch", QPointF(200, 100))
    ldr = scene.add_component("ldr", QPointF(300, 100))
    
    assert led is not None
    assert switch is not None
    assert ldr is not None
    
    # 1. Vérifier la présence et les coordonnées des broches
    assert hasattr(led, "anode_pin") and led.anode_pin is not None
    assert hasattr(switch, "pin1") and switch.pin1 is not None
    assert hasattr(ldr, "pin1") and ldr.pin1 is not None
    
    # 2. Clic sur la broche Anode de la LED
    anode_scene_pos = led.anode_pin.scenePos()
    view_pos_anode = view.mapFromScene(anode_scene_pos)
    press_event_1 = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(view_pos_anode),
        anode_scene_pos,
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    view.mousePressEvent(press_event_1)
    
    assert scene._pending_wire_start_pin == led.anode_pin
    
    # 3. Clic sur la broche Pin 1 du Switch pour finaliser le fil
    switch_scene_pos = switch.pin1.scenePos()
    view_pos_sw = view.mapFromScene(switch_scene_pos)
    press_event_2 = QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(view_pos_sw),
        switch_scene_pos,
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    )
    view.mousePressEvent(press_event_2)
    
    # Le fil direct doit avoir été créé entre la LED et le Switch !
    assert len(scene.connections) == 1
    conn = scene.connections[0]
    assert conn.from_component == led.component_id
    assert conn.from_pin == "anode"
    assert conn.to_component == switch.component_id
    assert conn.to_pin == "pin1"
    
    # 4. Clic sur la broche COM du Switch
    com_scene_pos = switch.pin_com.scenePos()
    view_pos_com = view.mapFromScene(com_scene_pos)
    view.mousePressEvent(QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(view_pos_com),
        com_scene_pos,
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    ))
    
    # 5. Clic sur la broche 1 du LDR
    ldr_scene_pos = ldr.pin1.scenePos()
    view_pos_ldr = view.mapFromScene(ldr_scene_pos)
    view.mousePressEvent(QMouseEvent(
        QMouseEvent.Type.MouseButtonPress,
        QPointF(view_pos_ldr),
        ldr_scene_pos,
        Qt.LeftButton,
        Qt.LeftButton,
        Qt.NoModifier,
    ))
    
    # Un second fil direct doit relier le Switch au LDR !
    assert len(scene.connections) == 2
    conn2 = scene.connections[1]
    assert conn2.from_component == switch.component_id
    assert conn2.from_pin == "com"
    assert conn2.to_component == ldr.component_id
    assert conn2.to_pin == "pin1"
    
    window.close()

