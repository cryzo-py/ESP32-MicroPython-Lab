"""
Classe de base pour le runtime des composants électroniques
"""

from typing import Any
from PySide6.QtCore import QObject, Signal


class BaseComponentRuntime(QObject):
    state_changed = Signal(dict)

    def __init__(self, component_id: str, properties: dict[str, Any] | None = None):
        super().__init__()
        self.component_id = component_id
        self.properties: dict[str, Any] = properties or {}

    def update_pin(self, pin_id: str, value: int | float):
        """Appelé lorsqu'une broche du composant reçoit un signal"""
        pass

    def get_pin_value(self, pin_id: str) -> int | float:
        """Retourne la valeur émise par une broche"""
        return 0
