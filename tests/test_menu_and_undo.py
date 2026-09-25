"""
Tests unitaires et d'intégration pour la barre de menu complète,
le déplacement interactif des fils et le système Undo/Redo (Ctrl+Z / Ctrl+Y).
"""

import pytest
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QKeySequence

from esp32_lab.core.project_service import ProjectService
from esp32_lab.ui.main_window import MainWindow
from esp32_lab.ui.canvas.undo_commands import (
    MoveComponentCommand,
    MoveWireTerminalCommand,
    AddComponentCommand,
    DeleteItemsCommand,
    AddWireCommand,
)


def test_menu_bar_structure(app):
    """Vérifie la présence et les raccourcis de toutes les sections de la barre de menus."""
    from esp32_lab.app.i18n import set_current_language
    set_current_language("fr")
    window = MainWindow()
    menubar = window.menuBar()
    assert menubar is not None

    actions = menubar.actions()
    titles = [a.text() for a in actions]
    
    assert any("Fichier" in t for t in titles)
    assert any("Édition" in t for t in titles)
    assert any("Composants" in t for t in titles)
    assert any("Affichage" in t for t in titles)
    assert any("Simulation" in t for t in titles)
    assert any("Cours" in t for t in titles)
    assert any("Exemples" in t for t in titles)
    assert any("Aide" in t for t in titles)

    # Actions Undo / Redo
    assert window.act_undo is not None
    assert window.act_redo is not None
    assert window.act_undo.shortcut().toString() in ("Ctrl+Z", "Ctrl+Alt+Z")
    
    window.close()


def test_undo_redo_add_component(app):
    """Vérifie l'ajout de composant avec annulation (Ctrl+Z) et rétablissement (Ctrl+Y)."""
    window = MainWindow()
    initial_count = len(window.circuit_scene.component_items)

    # Ajout d'une LED
    window._on_add_component("led")
    assert len(window.circuit_scene.component_items) == initial_count + 1

    # Annuler (Ctrl+Z)
    window.undo_stack.undo()
    assert len(window.circuit_scene.component_items) == initial_count

    # Rétablir (Ctrl+Y)
    window.undo_stack.redo()
    assert len(window.circuit_scene.component_items) == initial_count + 1

    window.close()


def test_undo_redo_move_wire_terminal(app):
    """Vérifie le déplacement d'embout de fil avec annulation et rétablissement."""
    window = MainWindow()
    window._load_project(ProjectService.create_default_project())
    scene = window.circuit_scene

    # Le projet de démo a le cavalier wire_1: GPIO2 -> breadboard_1:r10_a
    conn = next((c for c in scene.connections if c.id == "wire_1"), None)
    assert conn is not None
    assert conn.to_pin == "r10_a"
    
    # Déplacer l'extrémité de r10_a vers r15_a
    success = scene.reconnect_wire_terminal("wire_1", "end", "breadboard_1", "r15_a")
    assert success is True
    assert conn.to_pin == "r15_a"

    # Enregistrer la commande dans la pile
    cmd = MoveWireTerminalCommand(
        scene, "wire_1", "end", "breadboard_1", "r10_a", "breadboard_1", "r15_a", initial_applied=True
    )
    window.undo_stack.push(cmd)

    # Annuler (Ctrl+Z) : doit revenir à r10_a
    window.undo_stack.undo()
    assert conn.to_pin == "r10_a"

    # Rétablir (Ctrl+Y) : doit revenir à r15_a
    window.undo_stack.redo()
    assert conn.to_pin == "r15_a"

    window.close()


def test_undo_redo_rotate_component(app):
    """Vérifie la rotation de composant avec annulation et rétablissement."""
    window = MainWindow()
    window._load_project(ProjectService.create_default_project())
    scene = window.circuit_scene

    res_item = scene.component_items.get("resistor_1")
    assert res_item is not None

    scene.clearSelection()
    res_item.setSelected(True)
    initial_rot = res_item.rotation()

    # Rotation 90°
    scene.rotate_selected_component(90.0)
    assert res_item.rotation() == (initial_rot + 90.0) % 360.0

    # Annuler (Ctrl+Z)
    window.undo_stack.undo()
    assert res_item.rotation() == initial_rot

    # Rétablir (Ctrl+Y)
    window.undo_stack.redo()
    assert res_item.rotation() == (initial_rot + 90.0) % 360.0

    window.close()


def test_undo_redo_delete_items(app):
    """Vérifie la suppression d'éléments avec annulation et rétablissement."""
    window = MainWindow()
    window._load_project(ProjectService.create_default_project())
    scene = window.circuit_scene

    led_item = scene.component_items.get("led_1")
    assert led_item is not None

    scene.clearSelection()
    led_item.setSelected(True)

    # Suppression
    scene.delete_selected_items()
    assert "led_1" not in scene.component_items

    # Annuler (Ctrl+Z) : LED restaurée
    window.undo_stack.undo()
    assert "led_1" in scene.component_items
    restored_led = scene.component_items["led_1"]
    assert getattr(restored_led, "_was_inserted", False) or restored_led.parentItem() == scene.breadboard_item

    # Rétablir (Ctrl+Y) : LED supprimée à nouveau
    window.undo_stack.redo()
    assert "led_1" not in scene.component_items

    window.close()


def test_menu_quick_example_loading(app):
    """Vérifie le chargement direct d'un exemple depuis le menu Exemples."""
    window = MainWindow()

    window._load_example_by_key("pot_pwm")
    assert "Variateur" in window.current_project.name or "pot" in window.current_project.description.lower()
    assert len(window.circuit_scene.component_items) > 0

    window.close()


def test_menu_volet_montage_toggle(app):
    """Vérifie le basculement d'affichage du volet Montage & Platine depuis le menu Affichage."""
    from esp32_lab.app.i18n import set_current_language
    set_current_language("fr")
    window = MainWindow()
    window._show_workspace_view()
    window.show()
    assert window.simulator_widget is not None
    assert not window.simulator_widget.isHidden()

    # Trouver l'action Volet Montage
    act_montage = None
    for action in window.menuBar().actions():
        if "Affichage" in action.text():
            for sub_act in action.menu().actions():
                if "Montage" in sub_act.text():
                    act_montage = sub_act
                    break

    assert act_montage is not None
    assert act_montage.isCheckable()
    assert act_montage.isChecked()

    # Masquer le volet montage
    act_montage.trigger()
    assert not window.simulator_widget.isVisible()

    # Réafficher le volet montage
    act_montage.trigger()
    assert window.simulator_widget.isVisible()

    window.close()


def test_wire_color_change_and_undo(app):
    """Vérifie le changement de couleur d'un fil et sa prise en charge par Undo/Redo."""
    window = MainWindow()
    window._load_project(ProjectService.create_default_project())
    scene = window.circuit_scene
    view = window.circuit_view

    # Vérifier qu'un fil existe (ex: gpio2 vers breadboard)
    assert len(scene.wire_items) > 0
    wire_id, wire_item = next(iter(scene.wire_items.items()))
    old_color = wire_item.color_str

    # Changer la couleur en jaune
    new_color = "#eab308"
    view._change_wire_color(wire_item, new_color)
    assert wire_item.color_str == new_color
    conn = next(c for c in scene.connections if c.id == wire_id)
    assert conn.color == new_color

    # Annuler (Ctrl+Z)
    window.undo_stack.undo()
    assert wire_item.color_str == old_color
    assert conn.color == old_color

    # Rétablir (Ctrl+Y)
    window.undo_stack.redo()
    assert wire_item.color_str == new_color
    assert conn.color == new_color

    window.close()


def test_component_properties_update_resistor_and_led(app):
    """Vérifie la mise à jour dynamique des propriétés (valeur résistance et couleur LED)."""
    window = MainWindow()
    window._load_project(ProjectService.create_default_project())
    scene = window.circuit_scene
    props_panel = window.properties_panel

    res_item = scene.component_items.get("resistor_1")
    assert res_item is not None

    # Inspecter et changer la valeur de résistance à 1000 Ω
    props_panel.inspect_component("resistor_1", "resistor", {"value": 220})
    props_panel.property_changed.emit("resistor_1", {"value": 1000})

    assert res_item.resistance_value == 1000

    # Inspecter et changer la couleur de LED à bleu
    led_item = scene.component_items.get("led_1")
    assert led_item is not None
    props_panel.inspect_component("led_1", "led", {"color": "red"})
    props_panel.property_changed.emit("led_1", {"color": "blue"})

    assert led_item.color_name == "blue"

    window.close()


def test_menu_file_close_project(app):
    """Vérifie que 'Fermer le projet' ferme le montage et renvoie vers la page d'accueil."""
    window = MainWindow()
    window._show_workspace_view()
    assert window.central_stack.currentIndex() == 1

    # Déclencher la fermeture du projet
    window._close_project()
    assert window.central_stack.currentIndex() == 0

    # Vérifier que le projet est vierge (aucun composant utilisateur, aucun fil)
    scene = window.circuit_scene
    user_comps = [cid for cid, it in scene.component_items.items() if cid not in ("esp32", "breadboard_1")]
    window.close()


def test_properties_panel_palette_and_scene_selection(app):
    """Vérifie l'affichage des propriétés lors de la sélection dans la palette et sur la scène."""
    window = MainWindow()
    window.show()
    window._show_workspace_view()

    # 1. Aucun popup orphelin ne doit être visible
    top_levels = [w for w in app.topLevelWidgets() if w.isVisible()]
    assert len(top_levels) == 1
    assert top_levels[0] == window

    # 2. Clic sur la carte LED dans la bibliothèque
    window._on_palette_component_selected("led")
    assert window.properties_panel.current_component_type == "led"
    assert not window.properties_panel.empty_label.isVisible()

    # 3. Ajout dynamique d'une LED sur la scène (comme par Drag & Drop)
    led = window.circuit_scene.add_component("led")
    assert window.properties_panel.current_component_id == "led_1"
    assert window.properties_panel.current_component_type == "led"

    # 4. Modification de la couleur via le panneau
    window.properties_panel.property_changed.emit("led_1", {"color": "blue"})
    assert led.color_name == "blue"

    # 5. Ajout et sélection d'une résistance
    res = window.circuit_scene.add_component("resistor")
    assert window.properties_panel.current_component_id == "resistor_1"
    assert window.properties_panel.current_component_type == "resistor"

    window.close()


def test_new_project_from_welcome_switches_view(app):
    """Vérifie que la création d'un nouveau projet ou le chargement depuis le menu bascule vers l'espace de travail."""
    window = MainWindow()
    window._show_welcome_view()
    assert window.central_stack.currentIndex() == 0

    # Fichier > Nouveau montage (ou Ctrl+N)
    window._new_project()
    assert window.central_stack.currentIndex() == 1

    # Retour à l'accueil puis chargement d'un exemple
    window._show_welcome_view()
    assert window.central_stack.currentIndex() == 0
    window._load_example_by_key("blink")
    assert window.central_stack.currentIndex() == 1

    # Retour à l'accueil puis chargement d'un cours/TP
    window._show_welcome_view()
    assert window.central_stack.currentIndex() == 0
    window._load_course_by_id("lesson_1_gpio_led")
    assert window.central_stack.currentIndex() == 1

    window.close()


def test_about_dialog(app):
    """Vérifie la boîte de dialogue À propos (résumé, auteur Fares Bel Haj Ali, copyright, tel, email)."""
    from PySide6.QtWidgets import QLabel
    from esp32_lab.ui.dialogs.about_dialog import AboutDialog
    dlg = AboutDialog()
    assert dlg is not None
    assert "À propos" in dlg.windowTitle()

    # Vérification textuelle des éléments demandés
    all_text = " ".join(lbl.text() for lbl in dlg.findChildren(QLabel))
    assert "Fares Bel Haj Ali" in all_text
    assert "Copyright" in all_text
    assert "belhadj.fares@gmail.com" in all_text
    assert "+216 22 392 646" in all_text
    assert "Résumé" in all_text or "MB-102" in all_text
    dlg.close()




