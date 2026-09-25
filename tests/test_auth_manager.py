import os
import pytest
from pathlib import Path
from esp32_lab.core.auth_manager import AuthManager

@pytest.fixture
def temp_auth_config(tmp_path):
    config_file = tmp_path / 'auth_test.json'
    yield config_file
    if config_file.exists():
        config_file.unlink()

def test_auth_manager_lifecycle(temp_auth_config):
    manager = AuthManager(config_path=temp_auth_config)
    assert not manager.is_pin_set()
    assert not manager.verify_pin('1234')
    manager.set_pin('1234')
    assert manager.is_pin_set()
    assert manager.verify_pin('1234')
    assert not manager.verify_pin('0000')
    assert not manager.verify_pin('12345')
    with pytest.raises(ValueError):
        manager.set_pin('12')
    with pytest.raises(ValueError):
        manager.set_pin('abcd')
    manager.clear_pin()
    assert not manager.is_pin_set()
    assert not manager.verify_pin('1234')
