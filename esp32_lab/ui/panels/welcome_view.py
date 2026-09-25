"""
Écran d'accueil & Page de démarrage (WelcomeWidget) pour ESP32 MicroPython Lab.
Interface moderne inspirée d'Algo-Tun et des IDEs professionnels (VS Code / JetBrains).
"""

from pathlib import Path
from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ActionCard(QFrame):
    """Carte d'action cliquable avec icône, titre, description et effet de survol moderne."""

    clicked = Signal()

    def __init__(self, icon_str: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setObjectName("ActionCard")
        self.setStyleSheet("""
            #ActionCard {
                background-color: #1a2234;
                border: 1px solid #2a3449;
                border-radius: 8px;
                padding: 12px 16px;
            }
            #ActionCard:hover {
                background-color: #242f46;
                border: 1px solid #38bdf8;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        icon_lbl = QLabel(icon_str)
        icon_lbl.setStyleSheet("font-size: 28px; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_lbl)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #f8fafc; background: transparent;")
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent;")
        text_layout.addWidget(desc_lbl)

        layout.addLayout(text_layout, 1)

        arrow_lbl = QLabel("➔")
        arrow_lbl.setStyleSheet("font-size: 16px; color: #64748b; font-weight: bold; background: transparent;")
        layout.addWidget(arrow_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
            event.accept()
        else:
            super().mousePressEvent(event)


class WelcomeWidget(QWidget):
    """Vue d'accueil principale de l'application."""

    new_project_requested = Signal()
    open_project_requested = Signal()
    examples_requested = Signal()
    courses_requested = Signal()
    recent_file_selected = Signal(str)
    workspace_requested = Signal()
    teacher_dashboard_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("WelcomeWidget")
        self.theme_name = "dark"
        self._setup_ui()
        self.set_theme("dark")
        self.refresh_recent_files()

    def set_theme(self, theme_name: str):
        """Adapte les couleurs et contrastes de la page d'accueil au thème actif."""
        self.theme_name = theme_name
        is_light = (theme_name == "light")

        bg_col = "#f8fafc" if is_light else "#0f172a"
        self.setStyleSheet(f"""
            #WelcomeWidget {{
                background-color: {bg_col};
            }}
            #WelcomeWidget QLabel {{
                background: transparent;
            }}
        """)

        # Titre principal
        title_col = "#0f172a" if is_light else "#ffffff"
        self.title_label.setStyleSheet(f"font-size: 32px; font-weight: 800; color: {title_col}; letter-spacing: 0.5px;")

        # Slogan
        tagline_col = "#0284c7" if is_light else "#38bdf8"
        self.tagline_label.setStyleSheet(f"font-size: 15px; color: {tagline_col}; font-weight: 600;")

        # Sous-titre
        desc_col = "#475569" if is_light else "#94a3b8"
        self.desc_label.setStyleSheet(f"font-size: 12px; color: {desc_col}; font-weight: 500;")

        # Pillule raccourcis
        hint_bg = "#ffffff" if is_light else "#1e293b"
        hint_border = "#cbd5e1" if is_light else "#334155"
        hint_col = "#334155" if is_light else "#94a3b8"
        self.hint_label.setStyleSheet(f"""
            color: {hint_col};
            font-size: 12px;
            background-color: {hint_bg};
            border: 1px solid {hint_border};
            border-radius: 16px;
            padding: 6px 18px;
            margin-top: 10px;
        """)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(0)

        main_layout.addStretch(2)

        # Conteneur central élégant inspiré d'Algo-Tun
        center_container = QFrame(self)
        center_container.setObjectName("WelcomeCenterBox")
        center_container.setStyleSheet("""
            #WelcomeCenterBox {
                background-color: transparent;
                border: none;
            }
        """)
        center_layout = QVBoxLayout(center_container)
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(14)

        # 1. Logo officiel de l'application (grande taille, net)
        icon_path = Path(__file__).resolve().parent.parent.parent / "resources" / "icons" / "app_icon.png"
        logo_label = QLabel()
        if icon_path.exists():
            pix = QPixmap(str(icon_path)).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pix)
        else:
            logo_label.setText("💻")
            logo_label.setStyleSheet("font-size: 64px;")
        logo_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(logo_label)

        from ...app.i18n import tr

        # 2. Nom de l'application
        self.title_label = QLabel("ESP32 MicroPython Lab")
        self.title_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.title_label)

        # 3. Slogan
        self.tagline_label = QLabel(tr("welcome_tagline"))
        self.tagline_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.tagline_label)

        # 4. Sous-titre descriptif
        self.desc_label = QLabel(tr("welcome_desc"))
        self.desc_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.desc_label)

        # 5. Indication discrète des raccourcis
        self.hint_label = QLabel(tr("welcome_hint"))
        self.hint_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(self.hint_label, 0, Qt.AlignCenter)
        


        main_layout.addWidget(center_container, 0, Qt.AlignCenter)
        main_layout.addStretch(3)

        # Composants internes conservés pour compatibilité avec les tests et réglages
        self.recent_list = QListWidget(self)
        self.recent_list.itemClicked.connect(self._on_recent_item_clicked)
        self.recent_list.hide()
        self.empty_recent_lbl = QLabel(self)
        self.empty_recent_lbl.hide()

        settings = QSettings("ESP32Lab", "ESP32MicroPythonLab")
        show_on_start = settings.value("show_welcome_on_startup", True, type=bool)
        self.chk_startup = QCheckBox(tr("welcome_chk_startup"), self)
        self.chk_startup.setChecked(show_on_start)
        self.chk_startup.hide()
        self.chk_startup.toggled.connect(self._on_startup_checkbox_toggled)

    def set_language(self, lang: str = "fr"):
        """Met à jour les libellés de la page d'accueil selon la langue choisie."""
        from ...app.i18n import tr
        self.tagline_label.setText(tr("welcome_tagline"))
        self.desc_label.setText(tr("welcome_desc"))
        self.hint_label.setText(tr("welcome_hint"))
        self.chk_startup.setText(tr("welcome_chk_startup"))

    def _on_startup_checkbox_toggled(self, checked: bool):
        settings = QSettings("ESP32Lab", "ESP32MicroPythonLab")
        settings.setValue("show_welcome_on_startup", checked)

    def refresh_recent_files(self):
        """Actualise la liste des fichiers récemment ouverts."""
        self.recent_list.clear()
        settings = QSettings("ESP32Lab", "ESP32MicroPythonLab")
        files = settings.value("recent_files", [])
        if not isinstance(files, list):
            files = []

        valid_files = [f for f in files if isinstance(f, str) and f.strip()]
        for file_path in valid_files:
            p = Path(file_path)
            name = p.stem.replace("_", " ").title()
            item = QListWidgetItem(f"📄  {name}\n    {p.name}")
            item.setToolTip(file_path)
            item.setData(Qt.UserRole, file_path)
            self.recent_list.addItem(item)

    def _on_recent_item_clicked(self, item: QListWidgetItem):
        file_path = item.data(Qt.UserRole)
        if file_path:
            self.recent_file_selected.emit(file_path)
