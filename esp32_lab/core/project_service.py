"""
Service de gestion des projets (Création, Sauvegarde, Chargement, Exportation)
"""

import json
from pathlib import Path
import zipfile

from .models.board import create_default_esp32_wroom
from .models.component import ComponentModel, ComponentPin
from .models.connection import ConnectionModel
from .models.project import DEFAULT_MAIN_PY, ProjectModel


class ProjectService:
    @staticmethod
    def create_empty_project(name: str = "Nouveau Montage") -> ProjectModel:
        """Crée un projet totalement vierge (platine MB-102 prête, aucun composant branché, aucun fil)."""
        breadboard = ComponentModel(
            id="breadboard_1",
            type="breadboard",
            name="Platine d'essai",
            x=280,
            y=50,
            properties={"size": "half"},
        )
        return ProjectModel(
            name=name,
            description="Montage vierge à construire.",
            board_id="esp32_wroom_32",
            files={"main.py": "# ESP32 MicroPython Lab\n# Écrivez votre code MicroPython ici\n\n"},
            components=[breadboard],
            connections=[],
        )

    @staticmethod
    def create_default_project(name: str = "LED Clignotante ESP32") -> ProjectModel:
        """Crée un projet initial complet pour le scénario Blink (ESP32 + Breadboard + LED + Résistance sur GPIO 2)"""
        project = ProjectModel(
            name=name,
            description="Projet de démonstration : clignotement d'une LED connectée sur le GPIO 2 de l'ESP32.",
            board_id="esp32_wroom_32",
            files={"main.py": DEFAULT_MAIN_PY},
        )
        
        # Composant Breadboard
        breadboard = ComponentModel(
            id="breadboard_1",
            type="breadboard",
            name="Platine d'essai",
            x=280,
            y=50,
            properties={"size": "half"},
        )
        
        # Composant LED (rouge)
        led = ComponentModel(
            id="led_1",
            type="led",
            name="LED Rouge",
            x=334.5,
            y=129.0,
            properties={"color": "red", "state": False},
            pin_insertions={"anode": "r10_b", "cathode": "r11_b"}
        )
        
        # Composant Résistance (220 Ohms)
        resistor = ComponentModel(
            id="resistor_1",
            type="resistor",
            name="Résistance 220Ω",
            x=343.0,
            y=188.5,
            properties={"value": 220, "unit": "Ω"},
            pin_insertions={"pin1": "r11_c", "pin2": "r17_c"}
        )
        
        project.components.extend([breadboard, led, resistor])
        
        # Connexions (ESP32 GPIO 2 -> Ligne 10, Ligne 17 -> ESP32 GND)
        wire_signal = ConnectionModel(
            id="wire_1",
            from_component="esp32",
            from_pin="GPIO2",
            to_component="breadboard_1",
            to_pin="r10_a",
            color="#ef4444" # Rouge
        )
        wire_resistor = ConnectionModel(
            id="wire_2",
            from_component="breadboard_1",
            from_pin="r17_a",
            to_component="breadboard_1",
            to_pin="rail_l_minus_17",
            color="#1e293b" # Liaison directe
        )
        wire_gnd = ConnectionModel(
            id="wire_3",
            from_component="breadboard_1",
            from_pin="rail_l_minus_28",
            to_component="esp32",
            to_pin="GND_1",
            color="#0f172a" # Noir GND
        )
        project.connections.extend([wire_signal, wire_resistor, wire_gnd])
        
        return project

    @staticmethod
    def save_project(project: ProjectModel, file_path: str | Path) -> None:
        """Sauvegarde un projet sous format .lab32 (ou .esp32lab, ou .json)"""
        path = Path(file_path)
        data = project.to_dict()
        
        # Si extension .json, enregistre directement en JSON clair
        if path.suffix.lower() == ".json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return

        # Format standard .lab32 ou .esp32lab (Archive ZIP contenant project.json et les fichiers sources)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Écrire project.json
            zf.writestr("project.json", json.dumps(data, indent=2, ensure_ascii=False))
            # Écrire chaque fichier source à la racine de l'archive
            for filename, content in project.files.items():
                zf.writestr(filename, content)

    @staticmethod
    def load_project(file_path: str | Path) -> ProjectModel:
        """Charge un projet depuis un fichier .lab32, .esp32lab ou .json avec validation de robustesse."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Fichier de projet introuvable : {file_path}")

        # Vérifier si le fichier est vide
        if path.stat().st_size == 0:
            raise ValueError(f"Le fichier '{path.name}' est vide (0 octet). Impossible de charger le projet.")

        if path.suffix.lower() == ".json":
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return ProjectModel.from_dict(data)
            except json.JSONDecodeError as jde:
                raise ValueError(f"Le fichier JSON '{path.name}' est corrompu ou mal formé : {jde}")

        # Archive .lab32 ou .esp32lab
        try:
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path, "r") as zf:
                    if "project.json" not in zf.namelist():
                        raise ValueError(f"L'archive '{path.name}' ne contient pas le fichier de métadonnées obligatoire 'project.json'.")
                    project_json_content = zf.read("project.json").decode("utf-8")
                    data = json.loads(project_json_content)
                    project = ProjectModel.from_dict(data)
                    
                    # Recharger tous les fichiers sources présents dans l'archive
                    for file_info in zf.infolist():
                        if not file_info.is_dir() and file_info.filename != "project.json":
                            content = zf.read(file_info.filename).decode("utf-8")
                            project.files[file_info.filename] = content
                    
                    return project
            else:
                # Essai en JSON direct au cas où le fichier aurait été enregistré en texte brut
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return ProjectModel.from_dict(data)
        except (json.JSONDecodeError, zipfile.BadZipFile, UnicodeDecodeError) as ex:
            raise ValueError(f"Le fichier de projet '{path.name}' est endommagé ou corrompu : {ex}")
