"""Tests rigoureux de la fermeture du circuit électrique (continuité électrique et masse GND).

Vérifie que :
1. Une LED ne s'allume JAMAIS si le circuit est ouvert (absence de liaison GND ou VCC).
2. Le cas réel de l'utilisateur (Anode sur GPIO2, Cathode sur breadboard avec résistance mais sans retour GND)
   laisse la LED éteinte en permanence, même si GPIO2 clignote.
3. L'ajout du fil GND ferme le circuit et permet à la LED de clignoter.
4. Le retrait du fil GND éteint immédiatement la LED en temps réel.
5. Les montages Active-Low (Anode sur 3.3V, Cathode sur GPIO pilotée à 0) fonctionnent correctement.
6. Les courts-circuits (Anode et Cathode sur le même potentiel) maintiennent la LED éteinte.
7. Les composants en série (Résistances, Boutons, Interrupteurs, LDR) transmettent le potentiel
   uniquement lorsque le circuit est fermé.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPointF

# Ensure QApplication exists
app = QApplication.instance() or QApplication([])


def test_open_circuit_missing_gnd_keeps_led_off():
    """Vérifie que l'émission GPIO2=1 ne peut PAS allumer une LED dont la cathode n'est pas reliée à GND."""
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    from esp32_lab.core.models.connection import ConnectionModel

    scene = CircuitScene()
    scene.add_component("esp32", QPointF(0, 0))
    scene.add_component("breadboard", QPointF(350, 0))
    led = scene.add_component("led", QPointF(413.0, 79.0))

    # Fil reliant GPIO2 à l'anode via le trou r10_a
    conn_anode = ConnectionModel(
        id="w_anode",
        from_component="esp32", from_pin="GPIO2",
        to_component="breadboard_1", to_pin="r10_a",
        color="#38bdf8"
    )
    scene.connections.append(conn_anode)
    scene._create_wire_item(conn_anode)

    # AUCUN fil vers GND : le circuit est ouvert !
    assert not led.is_lit

    # Signal GPIO2 = 1 émis par MicroPython
    scene._on_gpio_changed(2, 1)

    # LA LED DOIT RESTER STRICTEMENT ÉTEINTE CAR LE CIRCUIT EST OUVERT
    assert led.is_lit is False
    assert led.is_on is False


def test_user_reproduction_resistor_without_gnd_keeps_led_off():
    """Reproduction exacte du cas utilisateur :
    GPIO2 -> LED Anode -> LED Cathode -> Résistance -> Rien (pas de liaison vers GND).
    La LED ne doit JAMAIS s'allumer ni clignoter.
    """
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    from esp32_lab.core.models.connection import ConnectionModel

    scene = CircuitScene()
    scene.add_component("esp32", QPointF(0, 0))
    scene.add_component("breadboard", QPointF(350, 0))

    # LED insérée en r10_b (anode) et r11_b (cathode)
    led = scene.add_component("led", QPointF(413.0, 79.0))

    # Résistance insérée entre r11_c (même strip que cathode) et r17_c
    res = scene.add_component("resistor", QPointF(404.5, 138.5))

    # Cavalier ESP32 GPIO2 -> r10_a (anode)
    conn_gpio = ConnectionModel(
        id="w_gpio",
        from_component="esp32", from_pin="GPIO2",
        to_component="breadboard_1", to_pin="r10_a",
        color="#38bdf8"
    )
    scene.connections.append(conn_gpio)
    scene._create_wire_item(conn_gpio)

    # Cavalier reliant r17_a au rail moins de la breadboard
    conn_rail = ConnectionModel(
        id="w_rail",
        from_component="breadboard_1", from_pin="r17_a",
        to_component="breadboard_1", to_pin="rail_l_minus_17",
        color="#1e293b"
    )
    scene.connections.append(conn_rail)
    scene._create_wire_item(conn_rail)

    # MAIS AUCUN FIL DE RETOUR DU RAIL MOINS VERS L'ESP32 GND ! (Circuit ouvert)

    # Clignotement simulé GPIO2 : 1 -> 0 -> 1 -> 0
    scene._on_gpio_changed(2, 1)
    assert led.is_lit is False, "La LED ne doit pas s'allumer sans retour GND !"

    scene._on_gpio_changed(2, 0)
    assert led.is_lit is False

    scene._on_gpio_changed(2, 1)
    assert led.is_lit is False


def test_closed_circuit_with_gnd_lights_led_and_blinks():
    """Vérifie que la fermeture du circuit (liaison vers GND) permet le fonctionnement normal."""
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    from esp32_lab.core.models.connection import ConnectionModel

    scene = CircuitScene()
    scene.add_component("esp32", QPointF(0, 0))
    scene.add_component("breadboard", QPointF(350, 0))
    led = scene.add_component("led", QPointF(413.0, 79.0))
    res = scene.add_component("resistor", QPointF(404.5, 138.5))

    # 1. Cavalier GPIO2 -> r10_a
    conn_gpio = ConnectionModel(
        id="w_gpio",
        from_component="esp32", from_pin="GPIO2",
        to_component="breadboard_1", to_pin="r10_a",
        color="#38bdf8"
    )
    scene.connections.append(conn_gpio)
    scene._create_wire_item(conn_gpio)

    # 2. Cavalier r17_a -> rail_l_minus_17
    conn_rail = ConnectionModel(
        id="w_rail",
        from_component="breadboard_1", from_pin="r17_a",
        to_component="breadboard_1", to_pin="rail_l_minus_17",
        color="#1e293b"
    )
    scene.connections.append(conn_rail)
    scene._create_wire_item(conn_rail)

    # 3. Cavalier de masse : rail_l_minus_28 -> ESP32 GND
    conn_gnd = ConnectionModel(
        id="w_gnd",
        from_component="breadboard_1", from_pin="rail_l_minus_28",
        to_component="esp32", to_pin="GND",
        color="#0f172a"
    )
    scene.connections.append(conn_gnd)
    scene._create_wire_item(conn_gnd)

    # Maintenant le circuit est FERMÉ !
    scene._on_gpio_changed(2, 1)
    assert led.is_lit is True, "La LED doit s'allumer quand le circuit est fermé et GPIO2=1"

    scene._on_gpio_changed(2, 0)
    assert led.is_lit is False, "La LED doit s'éteindre quand GPIO2=0"


def test_disconnecting_gnd_wire_turns_off_led_immediately():
    """Déconnecter le fil de masse en cours de fonctionnement éteint immédiatement la LED."""
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    from esp32_lab.core.models.connection import ConnectionModel

    scene = CircuitScene()
    scene.add_component("esp32", QPointF(0, 0))
    scene.add_component("breadboard", QPointF(350, 0))
    led = scene.add_component("led", QPointF(413.0, 79.0))

    conn_gpio = ConnectionModel(
        id="w_gpio",
        from_component="esp32", from_pin="GPIO2",
        to_component="breadboard_1", to_pin="r10_a",
        color="#38bdf8"
    )
    scene.connections.append(conn_gpio)
    scene._create_wire_item(conn_gpio)

    conn_gnd = ConnectionModel(
        id="w_gnd",
        from_component="breadboard_1", from_pin="r11_a",
        to_component="esp32", to_pin="GND",
        color="#0f172a"
    )
    scene.connections.append(conn_gnd)
    wire_gnd_item = scene._create_wire_item(conn_gnd)

    # Activer GPIO2 : la LED s'allume
    scene._on_gpio_changed(2, 1)
    assert led.is_lit is True

    # Retirer le fil GND pendant que GPIO2 est toujours à 1
    scene.removeItem(wire_gnd_item)
    scene.wire_items.pop("w_gnd", None)
    scene.connections = [c for c in scene.connections if c.id != "w_gnd"]
    scene.re_evaluate_topology()

    # La LED doit s'éteindre immédiatement !
    assert led.is_lit is False, "Le retrait du fil de masse doit couper le circuit et éteindre la LED !"


def test_active_low_led_configuration():
    """Vérifie le montage Active-Low : Anode sur 3.3V, Cathode sur GPIO."""
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    from esp32_lab.core.models.connection import ConnectionModel

    scene = CircuitScene()
    scene.add_component("esp32", QPointF(0, 0))
    scene.add_component("breadboard", QPointF(350, 0))
    led = scene.add_component("led", QPointF(413.0, 79.0))

    # Anode reliée au 3.3V
    conn_vcc = ConnectionModel(
        id="w_vcc",
        from_component="esp32", from_pin="3V3",
        to_component="breadboard_1", to_pin="r10_a",
        color="#ef4444"
    )
    scene.connections.append(conn_vcc)
    scene._create_wire_item(conn_vcc)

    # Cathode reliée à GPIO2
    conn_cathode = ConnectionModel(
        id="w_cat",
        from_component="breadboard_1", from_pin="r11_a",
        to_component="esp32", to_pin="GPIO2",
        color="#38bdf8"
    )
    scene.connections.append(conn_cathode)
    scene._create_wire_item(conn_cathode)

    # Initialement GPIO2 éteint / LOW -> Cathode à 0V, Anode à 3.3V -> LED ALLUMÉE !
    scene._on_gpio_changed(2, 0)
    assert led.is_lit is True, "En configuration active-low, GPIO2=0 doit allumer la LED !"

    # GPIO2 = 1 -> Cathode à 3.3V, Anode à 3.3V -> ddp = 0V -> LED ÉTEINTE !
    scene._on_gpio_changed(2, 1)
    assert led.is_lit is False, "En configuration active-low, GPIO2=1 doit éteindre la LED !"


def test_short_circuit_both_pins_same_strip_keeps_led_off():
    """Deux broches insérées sur la même bande équipotentielle ne produisent aucune ddp."""
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    from esp32_lab.core.models.connection import ConnectionModel

    scene = CircuitScene()
    scene.add_component("esp32", QPointF(0, 0))
    scene.add_component("breadboard", QPointF(350, 0))
    led = scene.add_component("led", QPointF(413.0, 79.0))

    # Forcer anode et cathode dans la même rangée (court-circuit interne)
    scene.topology.insert_pin(led.component_id, "anode", "r10_b")
    scene.topology.insert_pin(led.component_id, "cathode", "r10_d")

    conn_gpio = ConnectionModel(
        id="w1",
        from_component="esp32", from_pin="GPIO2",
        to_component="breadboard_1", to_pin="r10_a",
        color="#38bdf8"
    )
    scene.connections.append(conn_gpio)
    scene._create_wire_item(conn_gpio)

    scene._on_gpio_changed(2, 1)
    assert led.is_lit is False, "Une LED court-circuitée ne doit pas s'allumer !"


def test_slide_switch_controls_circuit():
    """Un interrupteur à glissière en série avec la LED commande l'allumage par contact mécanique."""
    from esp32_lab.ui.canvas.circuit_scene import CircuitScene
    from esp32_lab.core.models.connection import ConnectionModel

    scene = CircuitScene()
    scene.add_component("esp32", QPointF(0, 0))
    scene.add_component("breadboard", QPointF(350, 0))
    led = scene.add_component("led", QPointF(413.0, 79.0))

    # Ajouter interrupteur
    switch = scene.add_component("switch", QPointF(100, 100))
    # Interrupteur : COM relié à la cathode, pin2 relié à GND
    conn_sw1 = ConnectionModel(
        id="w_sw1",
        from_component="breadboard_1", from_pin="r11_a", # cathode
        to_component=switch.component_id, to_pin="com",
        color="#1e293b"
    )
    conn_sw2 = ConnectionModel(
        id="w_sw2",
        from_component=switch.component_id, from_pin="pin2",
        to_component="esp32", to_pin="GND",
        color="#0f172a"
    )
    conn_anode = ConnectionModel(
        id="w_anode",
        from_component="esp32", from_pin="GPIO2",
        to_component="breadboard_1", to_pin="r10_a",
        color="#38bdf8"
    )
    scene.connections.extend([conn_sw1, conn_sw2, conn_anode])

    # Interrupteur ouvert (is_on = False)
    switch.set_state(False)
    scene._on_gpio_changed(2, 1)
    assert led.is_lit is False, "Interrupteur ouvert : la LED doit être éteinte !"

    # Fermer l'interrupteur (is_on = True)
    switch.set_state(True)
    assert led.is_lit is True, "Interrupteur fermé : le circuit est fermé et la LED doit s'allumer !"

    # Rouvrir l'interrupteur
    switch.set_state(False)
    assert led.is_lit is False, "Réouverture de l'interrupteur : la LED doit s'éteindre !"
