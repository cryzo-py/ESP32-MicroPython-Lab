"""
Runtime pour le composant Bouton poussoir
"""

from .base import BaseComponentRuntime


class ButtonRuntime(BaseComponentRuntime):
    def __init__(self, component_id: str, properties: dict | None = None):
        super().__init__(component_id, properties)
        self.is_pressed = False

    def press(self):
        self.is_pressed = True
        self.state_changed.emit({
            "component_id": self.component_id,
            "is_pressed": True
        })

    def release(self):
        self.is_pressed = False
        self.state_changed.emit({
            "component_id": self.component_id,
            "is_pressed": False
        })

    def get_output_value(self) -> int:
        return 1 if self.is_pressed else 0
