"""
Écran de démarrage (Splash Screen) avec image et barre de progression pour ESP32 MicroPython Lab
"""

from pathlib import Path
from PySide6.QtCore import QPoint, QRectF, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class SplashScreen(QWidget):
    """Écran de démarrage moderne sans bordure avec logo officiel et barre de progression."""

    loading_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(520, 330)

        self._progress = 0
        self._steps = [
            (15, "Initialisation de l'environnement Qt & Thème..."),
            (35, "Chargement du moteur de simulation physique..."),
            (55, "Configuration de la platine MB-102 et du GPIO ESP32..."),
            (75, "Chargement de la bibliothèque de composants..."),
            (90, "Préparation de l'espace de travail..."),
            (100, "Laboratoire prêt !"),
        ]
        self._current_step_idx = 0
        self._target_window = None

        self._setup_ui()
        self._center_on_screen()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Conteneur principal avec fond sombre et bordure moderne
        container = QFrame(self)
        container.setObjectName("SplashCard")
        container.setStyleSheet("""
            #SplashCard {
                background-color: #0f172a;
                border: 1px solid #334155;
                border-radius: 14px;
            }
        """)

        card_layout = QVBoxLayout(container)
        card_layout.setContentsMargins(28, 26, 28, 24)
        card_layout.setSpacing(10)
        card_layout.setAlignment(Qt.AlignCenter)

        # 1. Logo officiel
        icon_path = Path(__file__).resolve().parent.parent / "resources" / "icons" / "app_icon.png"
        self.logo_label = QLabel()
        if icon_path.exists():
            pix = QPixmap(str(icon_path)).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText("💻")
            self.logo_label.setStyleSheet("font-size: 54px; background: transparent;")
        self.logo_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.logo_label)

        # 2. Nom de l'application
        self.title_label = QLabel("ESP32 MicroPython Lab")
        self.title_label.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;")
        self.title_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.title_label)

        # 3. Slogan & Badge
        self.tagline_label = QLabel("Laboratoire Virtuel de Programmation & Électronique")
        self.tagline_label.setStyleSheet("font-size: 12px; color: #38bdf8; font-weight: 600;")
        self.tagline_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.tagline_label)

        badge = QLabel("Édition Platine MB-102 & MicroPython Hardware Simulation")
        badge.setStyleSheet("""
            background-color: #1e293b;
            color: #94a3b8;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 2px 10px;
            font-size: 10px;
            font-weight: 600;
        """)
        badge.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(badge, 0, Qt.AlignCenter)

        card_layout.addSpacing(14)

        # 4. Label de statut dynamique
        self.status_label = QLabel("Démarrage du système...")
        self.status_label.setStyleSheet("font-size: 11px; color: #cbd5e1; font-weight: 500;")
        self.status_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(self.status_label)

        # 5. Barre de progression stylisée
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                text-align: center;
                font-size: 9px;
                font-weight: 700;
                color: #ffffff;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563eb, stop:1 #38bdf8
                );
                border-radius: 5px;
            }
        """)
        card_layout.addWidget(self.progress_bar)

        main_layout.addWidget(container)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(geo.x() + x, geo.y() + y)

    def set_progress(self, value: int, message: str = ""):
        """Met à jour manuellement la progression et le message de statut."""
        self._progress = max(0, min(100, value))
        self.progress_bar.setValue(self._progress)
        if message:
            self.status_label.setText(message)
        QApplication.processEvents()

    def start_loading(self, target_window=None, step_duration_ms: int = 180):
        """Lance l'animation de chargement progressive automatique."""
        self._target_window = target_window
        self._step_timer = QTimer(self)
        self._step_timer.setInterval(step_duration_ms)
        self._step_timer.timeout.connect(self._on_step_timeout)
        self.show()
        self._step_timer.start()

    def _on_step_timeout(self):
        if self._current_step_idx < len(self._steps):
            pct, msg = self._steps[self._current_step_idx]
            self.set_progress(pct, msg)
            self._current_step_idx += 1
        else:
            self._step_timer.stop()
            # Pause très courte avant de faire apparaître la fenêtre principale
            QTimer.singleShot(150, self._finish_loading)

    def _finish_loading(self):
        self.loading_finished.emit()
        if self._target_window:
            self._target_window.showMaximized()
        self.close()
