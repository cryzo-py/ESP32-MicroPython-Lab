from dataclasses import dataclass
from esp32_lab.core.app_state import AppState, AppMode
from esp32_lab.core.models.project import ProjectModel

@dataclass
class LockState:
    movement: bool = False
    deletion: bool = False
    rotation: bool = False
    interaction: bool = False
    properties: bool = False

class InteractionPolicy:
    def __init__(self, app_state: AppState):
        self._app_state = app_state
        self._locks: dict[str, LockState] = {}

    def set_app_state(self, app_state: AppState):
        self._app_state = app_state

    def load_from_project(self, project: ProjectModel) -> None:
        self._locks.clear()
        if project.pedagogy_profile is None:
            return
        
        locked_elements = project.pedagogy_profile.get('locked_elements', {})
        components = locked_elements.get('components', [])
        for comp_data in components:
            comp_id = comp_data.get('id')
            if not comp_id: continue
            
            locks = comp_data.get('locks', {})
            self._locks[comp_id] = LockState(
                movement=locks.get('move', False),
                deletion=locks.get('delete', False),
                rotation=locks.get('rotate', False),
                interaction=locks.get('interact', False),
                properties=locks.get('properties', False)
            )
            
        wires = locked_elements.get('wires', [])
        for wire_data in wires:
            wire_id = wire_data.get('id')
            if not wire_id: continue
            locks = wire_data.get('locks', {})
            self._locks[wire_id] = LockState(
                movement=locks.get('move', False),
                deletion=locks.get('delete', False)
            )

    def _is_action_denied(self, element_id: str, action_attr: str) -> bool:
        if self._app_state.mode == AppMode.TEACHER:
            return False
        lock_state = self._locks.get(element_id)
        if not lock_state:
            return False
        return getattr(lock_state, action_attr)

    def can_move(self, element_id: str) -> bool:
        return not self._is_action_denied(element_id, 'movement')

    def can_delete(self, element_id: str) -> bool:
        return not self._is_action_denied(element_id, 'deletion')

    def can_rotate(self, element_id: str) -> bool:
        return not self._is_action_denied(element_id, 'rotation')

    def can_interact(self, element_id: str) -> bool:
        return not self._is_action_denied(element_id, 'interaction')

    def can_edit_properties(self, element_id: str) -> bool:
        return not self._is_action_denied(element_id, 'properties')
