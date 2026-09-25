"""
Générateur de Nomenclature Industrielle (Bill of Materials - BOM Exporter).
Exporte la liste exhaustive des composants et consommables (résistances, diodes, capteurs, modules, fils)
en format CSV, Excel (CSV tabulé) ou HTML formatté pour intégration dans les dossiers techniques et commandes de pièces.
"""

import csv
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional
from .models.project import ProjectModel
from .models.connection import ConnectionModel


def classify_connection_wire(conn: ConnectionModel) -> str:
    """Détermine le type physique de câble Dupont nécessaire pour une liaison :
    - 'MM' : Mâle - Mâle (ex: Platine <-> Platine)
    - 'MF' : Mâle - Femelle (ex: Platine <-> ESP32 ou Platine <-> Module)
    - 'FF' : Femelle - Femelle (ex: ESP32 <-> Module direct sans platine)
    """
    def is_breadboard(comp_id: str) -> bool:
        cid = str(comp_id).lower()
        return "breadboard" in cid or cid.startswith("bb")

    start_is_bb = is_breadboard(conn.from_component)
    end_is_bb = is_breadboard(conn.to_component)

    if start_is_bb and end_is_bb:
        return "MM"
    elif start_is_bb or end_is_bb:
        return "MF"
    else:
        return "FF"


class BOMExporter:
    """Générateur de nomenclature (BOM) pour circuits électroniques ESP32."""

    COMPONENT_NAMES = {
        "esp32": "Carte de développement ESP32-WROOM-32 DevKit V1 (30 broches)",
        "breadboard": "Platine d'expérimentation sans soudure 830 points (MB-102)",
        "led": "Diode Électroluminescente (LED 5 mm)",
        "resistor": "Résistance à couche carbone 1/4W 5%",
        "button": "Bouton-Poussoir tactile 6x6 mm",
        "switch": "Interrupteur à glissière SPDT",
        "potentiometer": "Potentiomètre rotatif linéaire 10 kΩ",
        "joystick": "Module Joystick 2 axes analogiques + bouton",
        "buzzer": "Buzzer Piézoélectrique actif 5V",
        "relay": "Module Relais 1 canal 5V avec optocoupleur",
        "servo": "Micro Servomoteur SG90 (9g, rotation 0-180°)",
        "rgb_led": "LED RVB 5 mm (Cathode commune)",
        "neopixel": "Barrette / Ruban LED RVB adressable WS2812B",
        "oled": "Afficheur graphique OLED 0.96\" 128x64 I2C (SSD1306)",
        "lcd": "Écran alphanumérique LCD 1602 avec module I2C (PCF8574)",
        "ldr": "Photorésistance LDR GL5528",
        "pir": "Détecteur de mouvement pyroélectrique PIR (HC-SR501)",
        "dht22": "Capteur numérique de température et humidité (DHT22 / AM2302)",
        "hcsr04": "Capteur de distance à ultrasons (HC-SR04)",
        "bme280": "Capteur environnemental Pression / Température / Humidité I2C (BME280)",
        "mpu6050": "Centrale inertielle 6 axes Accéléromètre + Gyroscope I2C (MPU-6050)",
        "stepper": "Moteur pas-à-pas réducté 28BYJ-48 (5V) + Driver ULN2003",
        "tm1637": "Afficheur 4 digits 7 segments avec colonnes (TM1637)",
    }

    def generate_bom_data(self, project: ProjectModel) -> List[Dict]:
        """Agrège et standardise la liste des composants nécessaires pour le montage."""
        items: List[Dict] = []
        groups: Dict[str, list] = {}

        for c in project.components:
            ctype = str(c.type).lower().strip()
            # Distinguer les résistances par leur valeur
            if ctype in ("resistor", "resistance"):
                val = c.properties.get("value", 220)
                key = f"resistor_{val}"
            elif ctype == "led":
                col = c.properties.get("color", "Rouge").capitalize()
                key = f"led_{col}"
            else:
                key = ctype

            groups.setdefault(key, []).append(c)

        # 1. Composants actifs et passifs
        for key, comp_list in groups.items():
            first = comp_list[0]
            ctype = first.type.lower()
            qty = len(comp_list)
            ref_designators = ", ".join(c.id for c in comp_list)

            designation = self.COMPONENT_NAMES.get(ctype, f"Composant {ctype.upper()}")
            package = "Traversant THT"
            props_desc = ""

            if ctype in ("resistor", "resistance"):
                val = first.properties.get("value", 220)
                designation = f"Résistance 1/4W {val} Ω"
                props_desc = f"{val} Ω"
                package = "Axial 0.25W"
            elif ctype == "led":
                col = first.properties.get("color", "Rouge").capitalize()
                designation = f"LED 5 mm ({col})"
                props_desc = f"Couleur: {col}"
                package = "Radial 5mm"
            elif ctype == "neopixel":
                num = first.properties.get("num_leds", 8)
                props_desc = f"{num} pixels"
                package = "Module SMD 5050"

            items.append({
                "reference": ref_designators,
                "designation": designation,
                "quantity": qty,
                "package": package,
                "details": props_desc,
            })

        # 2. Consommables de câblage : Câbles Dupont ventilés par type (M-M, M-F, F-F)
        wire_types = Counter()
        wire_refs: Dict[str, List[str]] = {"MM": [], "MF": [], "FF": []}

        for c in project.connections:
            wtype = classify_connection_wire(c)
            wire_types[wtype] += 1
            wire_refs[wtype].append(c.id)

        wire_metadata = {
            "MM": ("Câbles de liaison souples Dupont (Mâle-Mâle)", "Cavalier pour platine d'expérimentation"),
            "MF": ("Câbles de liaison souples Dupont (Mâle-Femelle)", "Liaison Platine <-> Carte ESP32 / Module"),
            "FF": ("Câbles de liaison souples Dupont (Femelle-Femelle)", "Connexion directe Carte ESP32 <-> Module"),
        }

        for wtype in ("MM", "MF", "FF"):
            count = wire_types[wtype]
            if count > 0:
                designation, details_sub = wire_metadata[wtype]
                refs = ", ".join(wire_refs[wtype][:6])
                if count > 6:
                    refs += f", ... (+{count - 6})"
                items.append({
                    "reference": refs,
                    "designation": designation,
                    "quantity": count,
                    "package": "Filaire 20 cm (2.54 mm)",
                    "details": f"{count} liaison(s) — {details_sub}",
                })

        return items

    def export_csv(self, project: ProjectModel, file_path: Path) -> None:
        """Exporte la nomenclature en fichier CSV (encodage UTF-8 avec BOM pour Excel)."""
        data = self.generate_bom_data(project)
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Index", "Référence(s)", "Désignation du Composant", "Quantité", "Boîtier / Format", "Caractéristiques"])
            for idx, item in enumerate(data, 1):
                writer.writerow([
                    idx,
                    item["reference"],
                    item["designation"],
                    item["quantity"],
                    item["package"],
                    item["details"],
                ])
