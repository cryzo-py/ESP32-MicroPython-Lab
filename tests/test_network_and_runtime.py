"""
Tests automatisés pour le module network simulé et les imports MicroPython Pro.
"""

from esp32_lab.simulator.modules import network
from esp32_lab.simulator.gpio import GPIOManager
from esp32_lab.simulator.runtime import SimulationWorker


def test_network_wlan_sta_lifecycle():
    wlan = network.WLAN(network.STA_IF)
    assert not wlan.active()
    assert not wlan.isconnected()

    # Activation
    wlan.active(True)
    assert wlan.active()

    # Connexion
    wlan.connect("Mon_WiFi_Box", "motdepasse123")
    assert wlan.isconnected()
    assert wlan.status() == 1000

    # Test en mode Sandbox
    network.set_host_bridge_enabled(False)
    wlan = network.WLAN(network.STA_IF)
    wlan.connect("Mon_WiFi_Box", "motdepasse123")
    ip_sandbox, mask, gateway, dns = wlan.ifconfig()
    assert ip_sandbox.startswith("192.168.")

    # Test en mode Passerelle Réelle Hôte
    network.set_host_bridge_enabled(True)
    wlan.connect("Mon_WiFi_Box", "motdepasse123")
    ip_real, mask, gateway, dns = wlan.ifconfig()
    assert len(ip_real.split(".")) == 4
    assert mask == "255.255.255.0"

    # Scan des réseaux
    ap_list = wlan.scan()
    assert len(ap_list) >= 1

    # Déconnexion
    wlan.disconnect()
    assert not wlan.isconnected()


def test_runtime_imports_pro_modules():
    code = """
import network
import usocket as socket
import json
import ustruct as struct

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect("TestNet", "pass")
status = wlan.isconnected()
data = json.dumps({"connected": status})
"""
    gpio_mgr = GPIOManager()
    worker = SimulationWorker(code, gpio_mgr)
    
    outputs = []
    errors = []
    worker.output_received.connect(outputs.append)
    worker.error_occurred.connect(lambda msg, line: errors.append((msg, line)))

    worker.run()
    assert len(errors) == 0


def test_urequests_and_bluetooth_in_runtime():
    code = """
import bluetooth
import urequests

ble = bluetooth.BLE()
ble.active(True)
assert ble.active() is True
ble.config(gap_name="TestBLE")

# Test urequests API objects
resp = urequests.Response(200, "OK", b'{"status": "success", "temp": 24.5}', {"content-type": "application/json"})
assert resp.status_code == 200
assert resp.json()["status"] == "success"
assert resp.json()["temp"] == 24.5
"""
    gpio_mgr = GPIOManager()
    worker = SimulationWorker(code, gpio_mgr)

    errors = []
    worker.error_occurred.connect(lambda msg, line: errors.append((msg, line)))
    worker.run()
    assert len(errors) == 0
