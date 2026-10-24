"""
Boîte de dialogue de sélection des projets exemples (ExamplesDialog)
"""

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
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

        # En-tête et Filtre
        header_row = QHBoxLayout()
        title = QLabel("💡 Choisissez un exemple prêt à simuler :")
        title.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {fg_dlg}; background: transparent;")
        header_row.addWidget(title)
        header_row.addStretch()

        lbl_filter = QLabel("Filtre :")
        lbl_filter.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {desc_fg}; background: transparent;")
        header_row.addWidget(lbl_filter)

        self.combo_filter = QComboBox()
        self.combo_filter.addItems([
            "🌟 Tous les exemples",
            "⚡ Arduino Uno C++",
            "🐍 ESP32 MicroPython",
        ])
        combo_bg = "#f8fafc" if self.is_light else "#1e293b"
        combo_border = "#cbd5e1" if self.is_light else "#334155"
        self.combo_filter.setStyleSheet(f"""
            QComboBox {{
                background-color: {combo_bg};
                color: {fg_dlg};
                border: 1px solid {combo_border};
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        self.combo_filter.currentIndexChanged.connect(self._apply_filter)
        header_row.addWidget(self.combo_filter)
        main_layout.addLayout(header_row)

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

        self.all_examples_meta = [
            # Arduino Uno (C++)
            ("uno_blink", "⚡ 💡 LED Clignotante D13 (Arduino Uno)", "arduino_uno"),
            ("uno_button_led", "⚡ 🔘 Bouton Poussoir & LED (Arduino Uno)", "arduino_uno"),
            ("uno_pot_pwm", "⚡ 🎛️ Variateur PWM & Potentiomètre (Arduino Uno)", "arduino_uno"),
            ("uno_servo", "⚡ 🦾 Balayage Servomoteur SG90 (Arduino Uno)", "arduino_uno"),
            ("uno_traffic_lights", "⚡ 🚦 Feux Tricolores Routiers (Arduino Uno)", "arduino_uno"),
            ("uno_lcd", "⚡ 📟 Afficheur LCD 1602 (Arduino Uno)", "arduino_uno"),
            # ESP32 (MicroPython)
            ("blink", "🐍 💡 LED Clignotante (Blink)", "esp32_wroom_32"),
            ("button_led", "🐍 🔘 Bouton Poussoir & LED", "esp32_wroom_32"),
            ("pot_pwm", "🐍 🎛️ Variateur Potentiomètre & PWM", "esp32_wroom_32"),
            ("servo_sweep", "🐍 🦾 Balayage Servomoteur SG90", "esp32_wroom_32"),
            ("dht22_weather", "🐍 🌡️ Station Météo DHT22", "esp32_wroom_32"),
            ("oled_display", "🐍 📱 Écran OLED SSD1306 (I2C)", "esp32_wroom_32"),
            ("hcsr04_sonar", "🐍 🦇 Télémètre Ultrason HC-SR04", "esp32_wroom_32"),
            ("lcd_display", "🐍 📟 Afficheur LCD I2C 16x2", "esp32_wroom_32"),
            ("relay_control", "🐍 🔌 Module Relais 5V & Charge", "esp32_wroom_32"),
            ("neopixel_ring", "🐍 🌈 Anneau NeoPixel WS2812B", "esp32_wroom_32"),
            ("wifi_web_server", "🐍 📶 Wi-Fi & Serveur Web IoT", "esp32_wroom_32"),
            ("ble_beacon", "🐍 📡 Bluetooth Low Energy (BLE)", "esp32_wroom_32"),
            ("weather_cloud_iot", "🐍 🌦️ Station Météo Cloud IoT", "esp32_wroom_32"),
            ("wifi_scanner", "🐍 🔍 Scanner de Réseaux Wi-Fi", "esp32_wroom_32"),
            ("mqtt_client", "🐍 🌐 Client MQTT IoT (HiveMQ)", "esp32_wroom_32"),
            ("ble_scanner", "🐍 📱 Scanner Bluetooth BLE", "esp32_wroom_32"),
        ]

        self.filtered_examples = []
        self.list_widget.currentRowChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.list_widget)

        # Aperçu à droite
        preview_box = QWidget()
        preview_layout = QVBoxLayout(preview_box)
        preview_layout.setContentsMargins(8, 0, 0, 0)
        preview_layout.setSpacing(6)

        self.badge_platform = QLabel()
        self.badge_platform.setStyleSheet("""
            background-color: rgba(37, 99, 235, 0.15);
            color: #3b82f6;
            font-size: 11px;
            font-weight: bold;
            padding: 3px 8px;
            border-radius: 4px;
        """)
        preview_layout.addWidget(self.badge_platform)

        self.desc_label = QLabel()
        self.desc_label.setStyleSheet(f"color: {desc_fg}; font-style: italic; background: transparent;")
        self.desc_label.setWordWrap(True)
        preview_layout.addWidget(self.desc_label)

        self.code_title = QLabel("Code associé :")
        self.code_title.setStyleSheet(f"font-weight: 600; color: {code_title_fg}; margin-top: 6px; background: transparent;")
        preview_layout.addWidget(self.code_title)

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
        splitter.setSizes([270, 450])
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

        # Initialiser avec le filtre par défaut
        self._apply_filter(0)

    def _apply_filter(self, filter_idx: int):
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        self.filtered_examples = []

        target_board = None
        if filter_idx == 1:
            target_board = "arduino_uno"
        elif filter_idx == 2:
            target_board = "esp32_wroom_32"

        for key, label, board in self.all_examples_meta:
            if target_board is None or board == target_board:
                self.filtered_examples.append(key)
                item = QListWidgetItem(label)
                item.setData(Qt.UserRole, key)
                self.list_widget.addItem(item)

        self.list_widget.blockSignals(False)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            self._on_selection_changed(0)

    def _on_selection_changed(self, row: int):
        item = self.list_widget.item(row)
        if not item:
            return
        key = item.data(Qt.UserRole)
        proj = self.examples.get(key)
        if proj:
            self.desc_label.setText(proj.description)
            is_uno = (getattr(proj, "board_id", "") == "arduino_uno" or getattr(proj, "language", "") in ("arduino", "arduino_c", "c++", "cpp"))
            if is_uno:
                self.badge_platform.setText("⚡ Plateforme : Arduino Uno | Langage : C++ (sketch.ino)")
                self.badge_platform.setStyleSheet("""
                    background-color: rgba(14, 165, 233, 0.15);
                    color: #0284c7;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 3px 8px;
                    border-radius: 4px;
                """)
                self.code_title.setText("Code C++ Arduino associé (sketch.ino) :")
            else:
                self.badge_platform.setText("🐍 Plateforme : ESP32 DevKit V1 | Langage : MicroPython (main.py)")
                self.badge_platform.setStyleSheet("""
                    background-color: rgba(16, 185, 129, 0.15);
                    color: #059669;
                    font-size: 11px;
                    font-weight: bold;
                    padding: 3px 8px;
                    border-radius: 4px;
                """)
                self.code_title.setText("Code MicroPython associé (main.py) :")
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
