"""
Widget d'état et de détection de la carte ESP32 physique (HardwareStatusWidget)
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...app.event_bus import get_event_bus


class HardwareStatusWidget(QFrame):
    port_selected = Signal(str)
    rescan_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("HardwareCard")
        self.event_bus = get_event_bus()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # En-tête avec icône USB
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.title_label = QLabel("🔌 Carte physique")
        self.title_label.setObjectName("HardwareTitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Sélecteur de port + bouton rafraîchir
        port_layout = QHBoxLayout()
        port_layout.setContentsMargins(0, 0, 0, 0)
        port_layout.setSpacing(4)
        self.port_combo = QComboBox()
        self.port_combo.setPlaceholderText("Port COM...")
        self.port_combo.setStyleSheet("font-size: 11px; padding: 2px 4px;")
        self.port_combo.currentTextChanged.connect(self._on_port_changed)
        port_layout.addWidget(self.port_combo, 1)

        self.refresh_btn = QPushButton("↻")
        self.refresh_btn.setToolTip("Actualiser les ports COM")
        self.refresh_btn.setFixedSize(24, 22)
        self.refresh_btn.clicked.connect(self.rescan_requested)
        port_layout.addWidget(self.refresh_btn)

        layout.addLayout(port_layout)

        # Badge d'état
        self.status_badge = QLabel("ESP32 non connectée")
        self.status_badge.setObjectName("StatusBadgeDisconnected")
        self.status_badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_badge)

        # Barre de progression d'upload (masquée par défaut)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 4px;
                text-align: center;
                color: white;
                font-size: 10px;
                height: 14px;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Connexions EventBus
        self.event_bus.device_detection_updated.connect(self.update_ports)
        self.event_bus.device_connected.connect(self._on_device_connected)
        self.event_bus.device_disconnected.connect(self._on_device_disconnected)
        self.event_bus.upload_progress.connect(self._on_upload_progress)
        self.event_bus.upload_finished.connect(self._on_upload_finished)

        self.is_connected = False
        self.theme_name = "dark"
        self.set_theme("dark")

    def set_theme(self, theme_name: str):
        """Adapte les couleurs de la carte matérielle selon le thème."""
        self.theme_name = theme_name
        is_light = (theme_name == "light")
        title_col = "#0f172a" if is_light else "#f8fafc"
        self.title_label.setStyleSheet(f"font-weight: 700; color: {title_col}; font-size: 11px;")

        # Style badge
        if getattr(self, "is_connected", False):
            bg = "#dcfce7" if is_light else "#064e3b"
            fg = "#15803d" if is_light else "#34d399"
            border = "#86efac" if is_light else "#059669"
        else:
            bg = "#fee2e2" if is_light else "#3f1d24"
            fg = "#b91c1c" if is_light else "#f87171"
            border = "#fca5a5" if is_light else "#7f1d1d"

        self.status_badge.setStyleSheet(f"""
            background-color: {bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            padding: 5px 8px;
        """)

    def update_ports(self, ports: list[tuple[str, str]]):
        current = self.port_combo.currentData()
        self.port_combo.blockSignals(True)
        self.port_combo.clear()
        
        if not ports:
            self.port_combo.addItem("Aucun port série détecté", "")
            self._set_disconnected_state()
        else:
            for port, desc in ports:
                label = f"{port} - {desc}" if desc else port
                self.port_combo.addItem(label, port)
                
            # Rétablir la sélection précédente si possible
            idx = self.port_combo.findData(current)
            if idx != -1:
                self.port_combo.setCurrentIndex(idx)
            else:
                self.port_combo.setCurrentIndex(0)
                self.port_selected.emit(self.port_combo.currentData())

        self.port_combo.blockSignals(False)

    def _on_port_changed(self, _):
        port = self.port_combo.currentData()
        if port:
            self.port_selected.emit(port)

    def _on_device_connected(self, port_name: str):
        self.status_badge.setObjectName("StatusBadgeReady")
        self.status_badge.setText(f"✔ Prêt à téléverser ({port_name})")
        self.status_badge.setStyleSheet("""
            background-color: #064e3b;
            color: #34d399;
            border-radius: 6px;
            padding: 6px 10px;
            font-weight: 600;
        """)

    def _on_device_disconnected(self):
        self._set_disconnected_state()

    def _set_disconnected_state(self):
        self.status_badge.setObjectName("StatusBadgeDisconnected")
        self.status_badge.setText("● ESP32 non détectée")
        self.status_badge.setStyleSheet("""
            background-color: #3f1d24;
            color: #f87171;
            border-radius: 6px;
            padding: 6px 10px;
            font-weight: 600;
        """)

    def _on_upload_progress(self, percent: int, msg: str):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(f"{msg} ({percent}%)")

    def _on_upload_finished(self, success: bool, msg: str):
        self.progress_bar.setVisible(False)
        if success:
            self.status_badge.setText("✔ Téléversement réussi !")
        else:
            self.status_badge.setText(f"❌ Échec : {msg}")
