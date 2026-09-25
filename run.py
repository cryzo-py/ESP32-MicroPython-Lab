"""
Point d'entrée principal pour lancer l'application ESP32 MicroPython Lab
"""

import sys
import os
import ctypes
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from esp32_lab.app.theme import apply_theme
from esp32_lab.ui.main_window import MainWindow
from esp32_lab.ui.splash_screen import SplashScreen


def main():
    # Définition de l'AppUserModelID pour que la barre des tâches Windows affiche la vraie icône de l'application
    if sys.platform == "win32":
        try:
            myappid = "faresbelhajali.esp32lab.simulator.3.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    # Optimisation affichage haute résolution (High-DPI)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("ESP32 MicroPython Lab")
    app.setOrganizationName("ESP32Lab")

    # Icône globale de l'application
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).resolve().parent

    icon_dir = base_dir / "esp32_lab" / "resources" / "icons"
    icon_ico = icon_dir / "app_icon.ico"
    icon_png = icon_dir / "app_icon.png"
    icon_path = icon_ico if icon_ico.exists() else icon_png
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Application du thème sombre moderne
    apply_theme(app, "dark")

    # Écran de démarrage avec image et barre de progression
    splash = SplashScreen()
    window = MainWindow()

    # Si un fichier projet est passé en argument (ex: double-clic sur un .lab32 sous Windows)
    if len(sys.argv) > 1 and sys.argv[1] and not sys.argv[1].startswith("-"):
        file_arg = sys.argv[1]
        if os.path.exists(file_arg):
            window.open_project_file(file_arg)

    # Lance l'animation de chargement et affiche MainWindow à la fin
    splash.start_loading(target_window=window, step_duration_ms=140)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
