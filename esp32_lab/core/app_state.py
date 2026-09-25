from enum import Enum
from typing import Callable, List

class AppMode(Enum):
    STUDENT = "student"
    TEACHER = "teacher"

class AppState:
    """
    Gere l'etat global de l'application (Mode Eleve / Enseignant).
    Totalement agnostique de PySide6 et de l'authentification.
    """
    def __init__(self):
        self._mode = AppMode.STUDENT
        self._observers: List[Callable[[AppMode], None]] = []

    @property
    def mode(self) -> AppMode:
        return self._mode

    def is_teacher_mode_active(self) -> bool:
        return self._mode == AppMode.TEACHER

    def activate_teacher_mode(self) -> None:
        """Active le mode enseignant. Doit etre appele exclusivement par le service d'authentification."""
        if self._mode != AppMode.TEACHER:
            self._mode = AppMode.TEACHER
            self._notify_observers()

    def leave_teacher_mode(self) -> None:
        """Quitte le mode enseignant et retourne au mode etudiant."""
        if self._mode != AppMode.STUDENT:
            self._mode = AppMode.STUDENT
            self._notify_observers()

    def on_mode_changed(self, callback: Callable[[AppMode], None]) -> None:
        """Enregistre un callback pour observer les changements de mode (sans dependance a Qt)."""
        if callback not in self._observers:
            self._observers.append(callback)

    def _notify_observers(self) -> None:
        for observer in self._observers:
            observer(self._mode)
