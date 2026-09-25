"""
Panneau Console Série unifiée (ConsolePanelWidget)
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...app.event_bus import get_event_bus


class ConsolePanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_bus = get_event_bus()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Barre supérieure d'outils compacte
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(6)

        self.title_label = QLabel("💻 Console")
        self.title_label.setObjectName("ConsoleTitle")
        toolbar_layout.addWidget(self.title_label)

        toolbar_layout.addStretch()

        # Bouton Effacer
        self.clear_btn = QPushButton("🗑️")
        self.clear_btn.setToolTip("Effacer la console")
        self.clear_btn.setFixedSize(24, 22)
        self.clear_btn.clicked.connect(self.clear_console)
        toolbar_layout.addWidget(self.clear_btn)

        # Défilement automatique
        self.autoscroll_cb = QCheckBox("Auto")
        self.autoscroll_cb.setToolTip("Défilement automatique")
        self.autoscroll_cb.setChecked(True)
        toolbar_layout.addWidget(self.autoscroll_cb)

        # Choix Baudrate
        self.baudrate_combo = QComboBox()
        self.baudrate_combo.addItems(["9600", "115200"])
        self.baudrate_combo.setCurrentText("115200")
        self.baudrate_combo.setToolTip("Vitesse en bauds")
        self.baudrate_combo.setStyleSheet("font-size: 10px; padding: 1px 4px;")
        toolbar_layout.addWidget(self.baudrate_combo)

        layout.addLayout(toolbar_layout)

        # Zone d'affichage texte
        self.text_area = QPlainTextEdit()
        self.text_area.setObjectName("ConsoleTerminal")
        self.text_area.setReadOnly(True)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.text_area.setFont(font)
        self.text_area.setMaximumBlockCount(5000)  # Limiter la RAM
        layout.addWidget(self.text_area)

        # Barre de commande en bas
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(0, 0, 0, 0)
        self.cmd_input = QLineEdit()
        self.cmd_input.setObjectName("ConsoleInput")
        self.cmd_input.setPlaceholderText("Écrire une commande série...")
        self.cmd_input.returnPressed.connect(self._send_command)
        input_layout.addWidget(self.cmd_input)

        self.send_btn = QPushButton("➤")
        self.send_btn.setFixedWidth(36)
        self.send_btn.clicked.connect(self._send_command)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

        self.set_theme("dark")

        # Connexions EventBus
        self.event_bus.serial_data_received.connect(self.append_text)

    def set_theme(self, theme_name: str):
        """Adapte les couleurs de la console selon le thème."""
        is_light = (theme_name == "light")
        title_col = "#0f172a" if is_light else "#f8fafc"
        self.title_label.setStyleSheet(f"font-weight: 700; color: {title_col}; font-size: 11px;")

        cb_col = "#334155" if is_light else "#94a3b8"
        self.autoscroll_cb.setStyleSheet(f"font-size: 11px; color: {cb_col};")

        term_bg = "#f8fafc" if is_light else "#0b0f19"
        term_fg = "#0284c7" if is_light else "#38bdf8"
        term_border = "#cbd5e1" if is_light else "#1e293b"
        self.text_area.setStyleSheet(f"""
            QPlainTextEdit#ConsoleTerminal {{
                background-color: {term_bg};
                color: {term_fg};
                border: 1px solid {term_border};
                border-radius: 6px;
                padding: 4px;
            }}
        """)

        inp_bg = "#ffffff" if is_light else "#131b2e"
        inp_fg = "#0f172a" if is_light else "#f8fafc"
        inp_border = "#cbd5e1" if is_light else "#2a3449"
        self.cmd_input.setStyleSheet(f"""
            QLineEdit#ConsoleInput {{
                background-color: {inp_bg};
                color: {inp_fg};
                border: 1px solid {inp_border};
                border-radius: 4px;
                padding: 4px 8px;
            }}
        """)

        btn_bg = "#2563eb" if is_light else "#2563eb"
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_bg};
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 4px;
            }}
            QPushButton:hover {{
                background-color: #3b82f6;
            }}
        """)

    def append_text(self, text: str):
        self.text_area.moveCursor(QTextCursor.End)
        self.text_area.insertPlainText(text)
        if self.autoscroll_cb.isChecked():
            self.text_area.moveCursor(QTextCursor.End)

    def clear_console(self):
        self.text_area.clear()

    def _send_command(self):
        cmd = self.cmd_input.text()
        if cmd:
            self.append_text(f">>> {cmd}\n")
            self.event_bus.serial_data_to_send.emit(cmd)
            self.cmd_input.clear()
