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
    if sys.platform == "win32":
        try:
            myappid = "faresbelhajali.esp32lab.simulator.teacher.3.0"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception:
            pass

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName("ESP32 MicroPython Lab - Teacher Studio")
    app.setOrganizationName("ESP32Lab")

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).resolve().parent
    icon_path = base_dir / "esp32_lab" / "resources" / "icons" / "app_icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    apply_theme(app, "dark")
    splash = SplashScreen()
    window = MainWindow(app_profile="teacher")

    if len(sys.argv) > 1 and sys.argv[1] and not sys.argv[1].startswith("-"):
        if os.path.exists(sys.argv[1]):
            window.open_project_file(sys.argv[1])

    splash.start_loading(target_window=window, step_duration_ms=140)
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
