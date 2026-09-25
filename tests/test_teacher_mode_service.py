import pytest
from pathlib import Path
from esp32_lab.core.auth_manager import AuthManager
from esp32_lab.core.app_state import AppState, AppMode
from esp32_lab.application.auth.teacher_mode_service import TeacherModeService

@pytest.fixture
def temp_auth(tmp_path):
    config = tmp_path / 'test_auth.json'
    auth = AuthManager(config_path=config)
    auth.set_pin("4567")
    return auth

@pytest.fixture
def app_state():
    return AppState()

@pytest.fixture
def teacher_service(temp_auth, app_state):
    return TeacherModeService(auth_manager=temp_auth, app_state=app_state)

def test_initial_state(app_state):
    # 1 & 2. Etat initial = STUDENT, inactif au demarrage
    assert app_state.mode == AppMode.STUDENT
    assert not app_state.is_teacher_mode_active()

def test_activation_success(teacher_service, app_state):
    # 3. Activation avec authentification valide
    success = teacher_service.authenticate_teacher("4567")
    assert success is True
    assert app_state.mode == AppMode.TEACHER
    assert app_state.is_teacher_mode_active()

def test_activation_failure(teacher_service, app_state):
    # 4. Mauvais PIN : mode reste STUDENT
    success = teacher_service.authenticate_teacher("0000")
    assert success is False
    assert app_state.mode == AppMode.STUDENT

def test_leave_mode(teacher_service, app_state):
    # 5. Quitter teacher mode : retour STUDENT
    teacher_service.authenticate_teacher("4567")
    teacher_service.leave_teacher_mode()
    assert app_state.mode == AppMode.STUDENT

def test_multiple_activations(teacher_service, app_state):
    # 6 & 7. Plusieurs activations/sorties successives
    teacher_service.authenticate_teacher("4567")
    teacher_service.authenticate_teacher("4567")
    assert app_state.mode == AppMode.TEACHER
    
    teacher_service.leave_teacher_mode()
    teacher_service.leave_teacher_mode()
    assert app_state.mode == AppMode.STUDENT

def test_observer_pattern(app_state):
    # 8. Observation future (sans PySide6)
    history = []
    app_state.on_mode_changed(lambda mode: history.append(mode))
    
    app_state.activate_teacher_mode()
    app_state.leave_teacher_mode()
    
    assert history == [AppMode.TEACHER, AppMode.STUDENT]
