import subprocess
import time
from unittest.mock import MagicMock, patch
import pytest

from PySide6.QtWidgets import QApplication
from esp32_lab.hardware.arduino_cli import ArduinoCLIUploader
from esp32_lab.ui.main_window import MainWindow
from esp32_lab.core.models.project import ProjectModel


@pytest.fixture(scope="session")
def app():
    instance = QApplication.instance()
    if not instance:
        instance = QApplication([])
    return instance


def test_arduino_cli_uploader_initialization(app):
    mock_serial = MagicMock()
    uploader = ArduinoCLIUploader(mock_serial)
    assert uploader.serial_manager is mock_serial
    assert uploader.DEFAULT_FQBN == "arduino:avr:uno"


def test_arduino_cli_detection(app):
    with patch("shutil.which", return_value="C:/bin/arduino-cli.exe"):
        assert ArduinoCLIUploader.find_arduino_cli() == "C:/bin/arduino-cli.exe"
        uploader = ArduinoCLIUploader(MagicMock())
        assert uploader.is_available() is True

    with patch("shutil.which", return_value=None), \
         patch("pathlib.Path.is_file", return_value=False):
        assert ArduinoCLIUploader.find_arduino_cli() is None
        uploader = ArduinoCLIUploader(MagicMock())
        assert uploader.is_available() is False


def test_arduino_cli_missing_emits_guidance(app):
    mock_serial = MagicMock()
    mock_serial.current_port_name = "COM3"
    uploader = ArduinoCLIUploader(mock_serial)

    finished_results = []
    received_msgs = []
    uploader.upload_finished.connect(lambda ok, msg: finished_results.append((ok, msg)))
    uploader.event_bus.serial_data_received.connect(lambda msg: received_msgs.append(msg))

    with patch.object(ArduinoCLIUploader, "find_arduino_cli", return_value=None):
        uploader._do_compile_and_upload("void setup() {}", "COM3", "arduino:avr:uno")

    assert len(finished_results) == 1
    ok, msg = finished_results[0]
    assert ok is False
    assert "arduino-cli" in msg.lower()
    full_text = "".join(received_msgs)
    assert "winget install" in full_text or "arduino-cli" in full_text


def test_arduino_cli_compile_error(app):
    mock_serial = MagicMock()
    mock_serial.current_port_name = "COM3"
    uploader = ArduinoCLIUploader(mock_serial)

    finished_results = []
    received_msgs = []
    uploader.upload_finished.connect(lambda ok, msg: finished_results.append((ok, msg)))
    uploader.event_bus.serial_data_received.connect(lambda msg: received_msgs.append(msg))

    mock_comp_proc = MagicMock()
    mock_comp_proc.returncode = 1
    mock_comp_proc.stdout = ""
    mock_comp_proc.stderr = "sketch.ino:2:1: error: expected ';' before '}' token"

    with patch.object(ArduinoCLIUploader, "find_arduino_cli", return_value="arduino-cli"), \
         patch("subprocess.run", return_value=mock_comp_proc):
        uploader._do_compile_and_upload("void setup() { syntax error }", "COM3", "arduino:avr:uno")

    assert len(finished_results) == 1
    ok, msg = finished_results[0]
    assert ok is False
    assert "compilation" in msg.lower()
    full_text = "".join(received_msgs)
    assert "error" in full_text


def test_arduino_cli_successful_upload(app):
    mock_serial = MagicMock()
    mock_serial.current_port_name = "COM4"
    mock_serial.is_connected.return_value = True

    uploader = ArduinoCLIUploader(mock_serial)

    finished_results = []
    progress_records = []
    uploader.upload_finished.connect(lambda ok, msg: finished_results.append((ok, msg)))
    uploader.upload_progress.connect(lambda pct, msg: progress_records.append((pct, msg)))

    mock_ok_proc = MagicMock()
    mock_ok_proc.returncode = 0
    mock_ok_proc.stdout = "Success\n"
    mock_ok_proc.stderr = ""

    with patch.object(ArduinoCLIUploader, "find_arduino_cli", return_value="arduino-cli"), \
         patch("subprocess.run", return_value=mock_ok_proc):
        uploader._do_compile_and_upload("void setup() {} void loop() {}", "COM4", "arduino:avr:uno")

    assert len(finished_results) == 1
    ok, msg = finished_results[0]
    assert ok is True
    assert "réussi" in msg.lower() or "success" in msg.lower()

    # Port was disconnected then reconnected
    mock_serial.disconnect_port.assert_called_once()
    mock_serial.connect_port.assert_called_with("COM4")
    assert any(pct == 100 for pct, _ in progress_records)


def test_main_window_upload_dispatch(app):
    win = MainWindow()
    win.serial_manager.current_port_name = "COM5"

    with patch.object(win.uploader, "upload_code") as mock_esp_upload, \
         patch.object(win.arduino_uploader, "upload_code") as mock_ard_upload:
        
        # 1. Mode MicroPython (ESP32)
        win.combo_board.setCurrentIndex(0) # ESP32
        win.tabs.setCurrentIndex(0) # MicroPython
        win.py_editor.setPlainText("print('Upload Python')")
        win._upload_to_esp32()
        mock_esp_upload.assert_called_once()
        mock_ard_upload.assert_not_called()

        mock_esp_upload.reset_mock()
        mock_ard_upload.reset_mock()

        # 2. Mode Arduino Uno
        win.combo_board.setCurrentIndex(1) # Uno
        win.arduino_editor.setPlainText("void setup() {}")
        win._upload_to_esp32()
        mock_ard_upload.assert_called_once()
        mock_esp_upload.assert_not_called()
