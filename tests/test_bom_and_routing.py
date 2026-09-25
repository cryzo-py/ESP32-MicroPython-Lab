"""
Tests unitaires pour l'exportation de nomenclature BOM et le mode de routage orthogonal 90°.
"""

from pathlib import Path
from PySide6.QtCore import QPointF
from esp32_lab.core.bom_exporter import BOMExporter
from esp32_lab.core.models.component import ComponentModel
from esp32_lab.core.models.connection import ConnectionModel
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.ui.canvas.wire_item import WireGraphicsItem


def test_bom_exporter_aggregation(tmp_path):
    project = ProjectModel(id="test_proj", name="Projet Test BOM")
    project.components = [
        ComponentModel(id="esp32", type="esp32", name="ESP32"),
        ComponentModel(id="r1", type="resistor", name="R1", properties={"value": 220}),
        ComponentModel(id="r2", type="resistor", name="R2", properties={"value": 220}),
        ComponentModel(id="led_1", type="led", name="LED1", properties={"color": "red"}),
    ]
    project.connections = [
        ConnectionModel(from_component="esp32", from_pin="GPIO2", to_component="r1", to_pin="pin1"),
        ConnectionModel(from_component="r1", from_pin="pin2", to_component="led_1", to_pin="anode"),
        ConnectionModel(from_component="led_1", from_pin="cathode", to_component="esp32", to_pin="GND_1"),
    ]

    exporter = BOMExporter()
    bom_data = exporter.generate_bom_data(project)

    # 1 ESP32, 2 résistances 220Ω (agrégées), 1 LED rouge, 3 fils
    ref_map = {item["reference"]: item for item in bom_data}
    assert "r1, r2" in ref_map
    assert ref_map["r1, r2"]["quantity"] == 2
    assert "220" in ref_map["r1, r2"]["designation"]

    # Export CSV
    csv_file = tmp_path / "test_bom.csv"
    exporter.export_csv(project, csv_file)
    assert csv_file.exists()
    content = csv_file.read_text(encoding="utf-8-sig")
    assert "Résistance 1/4W 220 Ω" in content
    assert "Câbles de liaison souples Dupont" in content


def test_wire_orthogonal_routing():
    wire = WireGraphicsItem("conn_1", color="#38bdf8")
    wire.set_endpoints(QPointF(100, 100), QPointF(200, 200))
    assert not wire.is_orthogonal
    assert not wire.path().isEmpty()

    # Basculer en mode orthogonal
    wire.set_orthogonal_mode(True)
    assert wire.is_orthogonal
    path = wire.path()
    assert not path.isEmpty()
    # Le chemin comporte des segments droits
    assert path.elementCount() >= 4

    # Revenir en mode souple
    wire.set_orthogonal_mode(False)
    assert not wire.is_orthogonal


def test_dupont_wire_classification_and_bom_breakdown():
    from esp32_lab.core.bom_exporter import classify_connection_wire, BOMExporter

    # 1. Platine <-> Platine -> MM
    c_mm = ConnectionModel(from_component="breadboard_1", from_pin="r10_a", to_component="breadboard_1", to_pin="rail_l_minus_10")
    assert classify_connection_wire(c_mm) == "MM"

    # 2. Platine <-> ESP32 -> MF
    c_mf = ConnectionModel(from_component="esp32", from_pin="3V3", to_component="breadboard_1", to_pin="r1_a")
    assert classify_connection_wire(c_mf) == "MF"

    # 3. ESP32 <-> Module (connexion directe sans platine) -> FF
    c_ff = ConnectionModel(from_component="esp32", from_pin="GPIO21", to_component="oled_1", to_pin="sda")
    assert classify_connection_wire(c_ff) == "FF"

    # Vérification dans la nomenclature BOM
    proj = ProjectModel(id="p_test", name="Projet Test Dupont")
    proj.connections = [c_mm, c_mf, c_ff]
    exporter = BOMExporter()
    bom = exporter.generate_bom_data(proj)

    designations = [item["designation"] for item in bom]
    assert any("Mâle-Mâle" in d for d in designations)
    assert any("Mâle-Femelle" in d for d in designations)
    assert any("Femelle-Femelle" in d for d in designations)
