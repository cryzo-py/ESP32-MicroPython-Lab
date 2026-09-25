"""
Tests automatisés pour les modules Bluetooth (BLE) et MQTT (umqtt.simple)
"""

from esp32_lab.simulator.modules.umqtt.simple import MQTTClient
from esp32_lab.simulator.modules import bluetooth


def test_bluetooth_module():
    ble = bluetooth.BLE()
    assert ble.active() is False

    ble.active(True)
    assert ble.active() is True

    ble.config(gap_name="ESP32_Test")
    assert ble.config("gap_name") == "ESP32_Test"

    # Enregistrement service GATT
    srv_uuid = bluetooth.UUID("180D")  # Heart Rate Service
    char_uuid = bluetooth.UUID("2A37") # Measurement
    services = [(srv_uuid, [(char_uuid, bluetooth.FLAG_NOTIFY)])]
    handles = ble.gatts_register_services(services)
    assert len(handles) == 1
    char_handle = handles[0][0][0]

    # Écriture / Notification
    ble.gatts_write(char_handle, b"\x00\x48")
    val = ble.gatts_read(char_handle)
    assert val == b"\x00\x48"


def test_mqtt_client_initialization():
    client = MQTTClient("test_client", "broker.hivemq.com", port=1883)
    assert client.server == "broker.hivemq.com"
    assert client.port == 1883
    assert client.client_id == b"test_client"


def test_mqtt_runtime_execution():
    from esp32_lab.simulator.runtime import SimulationWorker
    from esp32_lab.simulator.gpio import GPIOManager

    code = """
import network
import time
from umqtt.simple import MQTTClient

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("test_wifi", "pass")

client = MQTTClient("test_id", "127.0.0.1", port=1883)
assert client.server == "127.0.0.1"
"""
    gpio_mgr = GPIOManager()
    worker = SimulationWorker(code, gpio_mgr)
    errors = []
    worker.error_occurred.connect(lambda msg, line: errors.append((msg, line)))
    worker.run()
    assert len(errors) == 0
