"""
Boîte de dialogue de sélection des projets exemples (ExamplesDialog)
"""

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ...core.examples import get_all_examples
from ...core.models.project import ProjectModel


class ExamplesDialog(QDialog):
    example_loaded = Signal(object) # ProjectModel

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bibliothèque d'exemples — ESP32 MicroPython Lab")
        self.resize(750, 480)

        settings = QSettings("ESP32Lab", "ESP32MicroPythonLab")
        self.is_light = (settings.value("theme", "dark") == "light")

        bg_dlg = "#ffffff" if self.is_light else "#0f172a"
        fg_dlg = "#0f172a" if self.is_light else "#f8fafc"
        list_bg = "#f8fafc" if self.is_light else "#1a2234"
        list_border = "#cbd5e1" if self.is_light else "#2a3449"
        list_item_border = "#e2e8f0" if self.is_light else "#242f46"
        list_item_hover = "#e2e8f0" if self.is_light else "#242f46"
        desc_fg = "#475569" if self.is_light else "#94a3b8"
        code_title_fg = "#1e293b" if self.is_light else "#cbd5e1"
        code_bg = "#f8fafc" if self.is_light else "#0b0f19"
        code_fg = "#0f172a" if self.is_light else "#38bdf8"
        code_border = "#cbd5e1" if self.is_light else "#1e293b"
        btn_cancel_bg = "#e2e8f0" if self.is_light else "#334155"
        btn_cancel_fg = "#0f172a" if self.is_light else "#f1f5f9"
        btn_cancel_border = "#cbd5e1" if self.is_light else "#475569"
        btn_cancel_hover = "#cbd5e1" if self.is_light else "#475569"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_dlg};
                color: {fg_dlg};
                font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            }}
            QLabel {{
                background: transparent;
                color: {fg_dlg};
            }}
        """)
        self.examples = get_all_examples()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # En-tête
        title = QLabel("💡 Choisissez un exemple prêt à simuler :")
        title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {fg_dlg}; background: transparent;")
        main_layout.addWidget(title)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Liste à gauche
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(f"""
            QListWidget {{
                background-color: {list_bg};
                border: 1px solid {list_border};
                border-radius: 6px;
                color: {fg_dlg};
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {list_item_border};
                color: {fg_dlg};
            }}
            QListWidget::item:hover {{
                background-color: {list_item_hover};
            }}
            QListWidget::item:selected {{
                background-color: #2563eb;
                color: white;
                font-weight: bold;
            }}
        """)

        examples_meta = [
            ("blink", "💡 LED Clignotante (Blink)"),
            ("button_led", "🔘 Bouton Poussoir & LED"),
            ("pot_pwm", "🎛️ Variateur Potentiomètre & PWM"),
            ("servo_sweep", "🦾 Balayage Servomoteur SG90"),
            ("dht22_weather", "🌡️ Station Météo DHT22"),
            ("oled_display", "📱 Écran OLED SSD1306 (I2C)"),
            ("hcsr04_sonar", "🦇 Télémètre Ultrason HC-SR04"),
            ("lcd_display", "📟 Afficheur LCD I2C 16x2"),
            ("relay_control", "🔌 Module Relais 5V & Charge"),
            ("neopixel_ring", "🌈 Anneau NeoPixel WS2812B"),
            ("wifi_web_server", "📶 Wi-Fi & Serveur Web IoT"),
            ("ble_beacon", "📡 Bluetooth Low Energy (BLE)"),
            ("weather_cloud_iot", "🌦️ Station Météo Cloud IoT (API Réelle)"),
            ("wifi_scanner", "🔍 Scanner de Réseaux Wi-Fi"),
            ("mqtt_client", "🌐 Client MQTT IoT (Télémétrie Cloud)"),
            ("ble_scanner", "📱 Scanner de Périphériques Bluetooth"),
        ]

        for key, label in examples_meta:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, key)
            self.list_widget.addItem(item)

        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.list_widget)

        # Aperçu à droite
        preview_box = QWidget()
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(8, 0, 0, 0)
        preview_layout.setSpacing(6)

        self.desc_label = QLabel()
        self.desc_label.setStyleSheet(f"color: {desc_fg}; font-style: italic; background: transparent;")
        self.desc_label.setWordWrap(True)
        preview_layout.addWidget(self.desc_label)

        code_title = QLabel("Code MicroPython associé :")
        code_title.setStyleSheet(f"font-weight: 600; color: {code_title_fg}; margin-top: 6px; background: transparent;")
        preview_layout.addWidget(code_title)

        self.code_preview = QPlainTextEdit()
        self.code_preview.setReadOnly(True)
        self.code_preview.setStyleSheet(f"""
            background-color: {code_bg};
            color: {code_fg};
            border: 1px solid {code_border};
            border-radius: 6px;
            font-family: Consolas, monospace;
            font-size: 11px;
        """)
        preview_layout.addWidget(self.code_preview)

        splitter.addWidget(preview_box)
        splitter.setSizes([260, 460])
        main_layout.addWidget(splitter, 1)

        # Boutons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        btn_cancel = QPushButton("Annuler")
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_cancel_bg};
                color: {btn_cancel_fg};
                border: 1px solid {btn_cancel_border};
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {btn_cancel_hover};
            }}
        """)
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_cancel)

        self.btn_load = QPushButton("🚀 Charger cet exemple")
        self.btn_load.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: white;
                font-weight: bold;
                padding: 8px 18px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #22c55e;
            }
        """)
        self.btn_load.clicked.connect(self._load_selected)
        btn_box.addWidget(self.btn_load)

        main_layout.addLayout(btn_box)

        # Sélectionner le premier par défaut
        self.list_widget.setCurrentRow(0)

    def _on_selection_changed(self, row: int):
        item = self.list_widget.item(row)
        if not item:
            return
        key = item.data(Qt.UserRole)
        proj = self.examples.get(key)
        if proj:
            self.desc_label.setText(proj.description)
            self.code_preview.setPlainText(proj.get_main_code())

    def _load_selected(self):
        row = self.list_widget.currentRow()
        item = self.list_widget.item(row)
        if item:
            key = item.data(Qt.UserRole)
            proj = self.examples.get(key)
            if proj:
                self.example_loaded.emit(proj)
                self.accept()
