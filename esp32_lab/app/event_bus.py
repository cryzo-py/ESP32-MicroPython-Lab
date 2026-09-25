"""
Bus d'événements central (Signaux Qt) pour découpler les modules de l'application
"""

from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    # Événements Projet
    project_loaded = Signal(object)      # Project
    project_saved = Signal(str)          # File path
    project_modified = Signal()

    # Événements Éditeur
    code_changed = Signal(str)           # Nouveau code
    request_simulation_start = Signal()
    request_simulation_stop = Signal()
    request_simulation_reset = Signal()
    request_upload = Signal()

    # Événements Circuit
    component_added = Signal(object)     # Component
    component_removed = Signal(str)      # Component ID
    component_moved = Signal(str, float, float) # id, x, y
    component_rotated = Signal(str, float)      # id, angle
    component_property_changed = Signal(str, dict) # id, properties
    wire_added = Signal(object)          # Connection
    wire_removed = Signal(str)           # Connection ID
    connection_updated = Signal(object)  # Connection
    topology_updated = Signal(object, dict) # ElectricalNetResolver, device_models dict

    # Événements Simulation & Matériel virtuel
    simulation_started = Signal()
    simulation_stopped = Signal()
    simulation_paused = Signal()
    simulation_error = Signal(str, int)  # Message, numéro de ligne
    gpio_changed = Signal(int, int)      # Pin number, state (0 or 1)
    analog_changed = Signal(int, int)    # Pin number, raw ADC value (0-4095)
    pwm_changed = Signal(int, int, int)  # Pin number, freq, duty
    display_updated = Signal(str, int, int, bytes)  # component_id, width, height, buffer

    # Événements Console & Port Série
    serial_data_received = Signal(str)   # Texte reçu (simulé ou matériel)
    serial_data_to_send = Signal(str)    # Commande envoyée par l'utilisateur
    repl_data_received = Signal(str)     # Sortie REPL
    repl_data_to_send = Signal(str)      # Commande REPL

    # Événements Matériel Physique (ESP32)
    device_connected = Signal(str)       # Port (ex: "COM4")
    device_disconnected = Signal()
    device_detection_updated = Signal(list) # Liste des ports disponibles
    usb_hardware_detected = Signal(bool, str) # Présence matérielle détectée (True/False, port_name)
    upload_started = Signal()
    upload_progress = Signal(int, str)   # Pourcentage (0-100), message d'état
    upload_finished = Signal(bool, str)  # Succès (True/False), message

    # Événements Règles Électriques (ERC)
    erc_violations_updated = Signal(list) # Liste des objets ERCViolation
    session_locked = Signal(dict)


_instance: EventBus | None = None


def get_event_bus() -> EventBus:
    global _instance
    if _instance is None:
        _instance = EventBus()
    return _instance


def reset_event_bus() -> None:
    """Réinitialise l'instance globale du bus d'événements (utile pour les tests unitaires)"""
    global _instance
    if _instance is not None:
        _instance.deleteLater()
        _instance = None
