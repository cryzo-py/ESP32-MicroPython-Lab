"""
Panneau d'inspection et modification des propriétés des composants (PropertiesPanelWidget)
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...app.event_bus import get_event_bus
from ...simulator.modules.dht import set_sensor_data


class PropertiesPanelWidget(QFrame):
    property_changed = Signal(str, dict) # component_id, updated_props

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PropertiesPanel")
        self.event_bus = get_event_bus()
        self.current_component_id: str | None = None
        self.current_component_type: str | None = None

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        # En-tête
        header = QHBoxLayout()
        self.title_label = QLabel("⚙ Propriétés")
        self.title_label.setObjectName("PropertiesPanelTitle")
        header.addWidget(self.title_label)
        header.addStretch()
        self.main_layout.addLayout(header)

        # Zone de formulaire dynamique
        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        self.form_layout.setContentsMargins(0, 0, 0, 0)
        self.form_layout.setSpacing(8)
        self.main_layout.addWidget(self.form_container)

        self.empty_label = QLabel("👉 Cliquez sur un composant sur la platine (ex: Résistance, LED, DHT22...) pour afficher et ajuster ses paramètres en direct.")
        self.empty_label.setObjectName("PropertiesEmptyLabel")
        self.empty_label.setWordWrap(True)
        self.main_layout.addWidget(self.empty_label)

        self.main_layout.addStretch()

    def inspect_component(self, comp_id: str, comp_type: str, props: dict):
        self.current_component_id = comp_id
        self.current_component_type = comp_type

        # Vider le formulaire existant
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)

        self.empty_label.setVisible(False)
        self.title_label.setText(f"⚙ {comp_type.capitalize()} ({comp_id})")

        if comp_type == "dht22":
            # Curseurs Température et Humidité
            temp = float(props.get("temperature", 24.5))
            hum = float(props.get("humidity", 55.0))

            temp_slider = QSlider(Qt.Horizontal)
            temp_slider.setRange(-20, 60)
            temp_slider.setValue(int(temp))
            temp_val_lbl = QLabel(f"{temp:.1f}°C")
            temp_val_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")

            def on_temp_change(val):
                temp_val_lbl.setText(f"{val:.1f}°C")
                props["temperature"] = float(val)
                set_sensor_data(props.get("connected_pin", 4), float(val), props.get("humidity", 50.0))
                self.property_changed.emit(comp_id, props)

            temp_slider.valueChanged.connect(on_temp_change)
            temp_box = QHBoxLayout()
            temp_box.addWidget(temp_slider)
            temp_box.addWidget(temp_val_lbl)
            self.form_layout.addRow("Température :", temp_box)

            hum_slider = QSlider(Qt.Horizontal)
            hum_slider.setRange(0, 100)
            hum_slider.setValue(int(hum))
            hum_val_lbl = QLabel(f"{hum:.0f}%")
            hum_val_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")

            def on_hum_change(val):
                hum_val_lbl.setText(f"{val}%")
                props["humidity"] = float(val)
                set_sensor_data(props.get("connected_pin", 4), props.get("temperature", 24.0), float(val))
                self.property_changed.emit(comp_id, props)

            hum_slider.valueChanged.connect(on_hum_change)
            hum_box = QHBoxLayout()
            hum_box.addWidget(hum_slider)
            hum_box.addWidget(hum_val_lbl)
            self.form_layout.addRow("Humidité :", hum_box)

        elif comp_type == "potentiometer":
            val = int(props.get("raw_value", 2048))
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 4095)
            slider.setValue(val)
            val_lbl = QLabel(f"{val} ({round(val * 3.3 / 4095, 2)}V)")
            val_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")

            def on_pot_change(v):
                val_lbl.setText(f"{v} ({round(v * 3.3 / 4095, 2)}V)")
                props["raw_value"] = v
                self.property_changed.emit(comp_id, props)

            slider.valueChanged.connect(on_pot_change)
            box = QHBoxLayout()
            box.addWidget(slider)
            box.addWidget(val_lbl)
            self.form_layout.addRow("Valeur ADC :", box)

        elif comp_type == "resistor":
            val_spin = QSpinBox()
            val_spin.setRange(10, 1000000)
            val_spin.setValue(int(props.get("value", 220)))
            val_spin.setSuffix(" Ω")

            def on_res_change(v):
                props["value"] = v
                self.property_changed.emit(comp_id, props)

            val_spin.valueChanged.connect(on_res_change)
            self.form_layout.addRow("Résistance :", val_spin)

        elif comp_type == "led":
            color_combo = QComboBox()
            color_combo.addItems(["red", "green", "blue", "yellow"])
            color_combo.setCurrentText(props.get("color", "red"))

            def on_color_change(c):
                props["color"] = c
                self.property_changed.emit(comp_id, props)

            color_combo.currentTextChanged.connect(on_color_change)
            self.form_layout.addRow("Couleur :", color_combo)

        elif comp_type == "servo":
            angle = float(props.get("angle", 90.0))
            angle_lbl = QLabel(f"{angle:.0f}°")
            angle_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")
            self.form_layout.addRow("Angle actuel :", angle_lbl)

        elif comp_type == "oled":
            res_lbl = QLabel("128 x 64 pixels (I2C)")
            res_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")
            self.form_layout.addRow("Résolution :", res_lbl)
            addr_lbl = QLabel("0x3C")
            self.form_layout.addRow("Adresse :", addr_lbl)

        elif comp_type == "hcsr04":
            dist = float(props.get("distance_cm", 25.0))
            dist_slider = QSlider(Qt.Horizontal)
            dist_slider.setRange(2, 400)
            dist_slider.setValue(int(dist))
            dist_val_lbl = QLabel(f"{dist:.1f} cm")
            dist_val_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")

            def on_dist_change(v):
                dist_val_lbl.setText(f"{v:.1f} cm")
                props["distance_cm"] = float(v)
                from ...simulator.modules.hcsr04 import set_distance
                set_distance(props.get("trig_pin", 5), props.get("echo_pin", 18), float(v))
                self.property_changed.emit(comp_id, props)

            dist_slider.valueChanged.connect(on_dist_change)
            box = QHBoxLayout()
            box.addWidget(dist_slider)
            box.addWidget(dist_val_lbl)
            self.form_layout.addRow("Distance :", box)

        elif comp_type in ("lcd", "lcd16x2"):
            l_lbl = QLabel("16 colonnes x 2 lignes (I2C)")
            l_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")
            self.form_layout.addRow("Format :", l_lbl)
            self.form_layout.addRow("Adresse :", QLabel("0x27"))

        elif comp_type in ("ldr", "photoresistor"):
            lux = float(props.get("lux", 300.0))
            lux_slider = QSlider(Qt.Horizontal)
            lux_slider.setRange(0, 1000)
            lux_slider.setValue(int(lux))
            
            # Calcul résistance
            r_approx = max(200.0, 500_000.0 / (lux + 5.0)) if lux > 0 else 1_000_000.0
            r_text = f"{r_approx/1000:.1f} kΩ" if r_approx >= 1000 else f"{int(r_approx)} Ω"
            lux_val_lbl = QLabel(f"{lux:.0f} Lux ({r_text})")
            lux_val_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")

            def on_lux_change(v):
                r = max(200.0, 500_000.0 / (v + 5.0)) if v > 0 else 1_000_000.0
                rtxt = f"{r/1000:.1f} kΩ" if r >= 1000 else f"{int(r)} Ω"
                lux_val_lbl.setText(f"{v} Lux ({rtxt})")
                props["lux"] = float(v)
                props["resistance"] = r
                self.property_changed.emit(comp_id, props)

            lux_slider.valueChanged.connect(on_lux_change)
            box = QHBoxLayout()
            box.addWidget(lux_slider)
            box.addWidget(lux_val_lbl)
            self.form_layout.addRow("Éclairement :", box)

        elif comp_type in ("rgb_led", "rgbled"):
            r_val = int(props.get("r", 255))
            g_val = int(props.get("g", 0))
            b_val = int(props.get("b", 0))

            preview_box = QLabel()
            preview_box.setFixedHeight(24)
            preview_box.setStyleSheet(f"background-color: rgb({r_val}, {g_val}, {b_val}); border-radius: 4px; border: 1px solid #475569;")
            self.form_layout.addRow("Aperçu couleur :", preview_box)

            # Curseurs R, G, B
            for ch_name, init_val, col in [("Rouge (R)", r_val, "#ef4444"), ("Vert (G)", g_val, "#22c55e"), ("Bleu (B)", b_val, "#3b82f6")]:
                slider = QSlider(Qt.Horizontal)
                slider.setRange(0, 255)
                slider.setValue(init_val)
                v_lbl = QLabel(str(init_val))
                v_lbl.setStyleSheet(f"color: {col}; font-weight: bold; min-width: 30px;")

                def make_cb(ch, label_w):
                    def cb(v):
                        label_w.setText(str(v))
                        k = "r" if "R" in ch else ("g" if "G" in ch else "b")
                        props[k] = v
                        r_cur = int(props.get("r", 0))
                        g_cur = int(props.get("g", 0))
                        b_cur = int(props.get("b", 0))
                        preview_box.setStyleSheet(f"background-color: rgb({r_cur}, {g_cur}, {b_cur}); border-radius: 4px; border: 1px solid #475569;")
                        self.property_changed.emit(comp_id, props)
                    return cb

                slider.valueChanged.connect(make_cb(ch_name, v_lbl))
                h = QHBoxLayout()
                h.addWidget(slider)
                h.addWidget(v_lbl)
                self.form_layout.addRow(f"{ch_name} :", h)

        elif comp_type in ("pir", "motion_sensor"):
            status_lbl = QLabel("En veille (aucun mouvement)")
            status_lbl.setStyleSheet("color: #94a3b8; font-weight: bold;")
            self.form_layout.addRow("État actuel :", status_lbl)

            trigger_btn = QPushButton("🏃 Déclencher un mouvement (3s)")
            trigger_btn.setCursor(Qt.PointingHandCursor)
            trigger_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2563eb;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #3b82f6;
                }
            """)

            def on_trigger():
                status_lbl.setText("🚨 Mouvement détecté (HIGH) !")
                status_lbl.setStyleSheet("color: #ef4444; font-weight: bold;")
                props["motion_detected"] = True
                self.property_changed.emit(comp_id, props)
                from PySide6.QtCore import QTimer
                QTimer.singleShot(3000, lambda: (
                    status_lbl.setText("En veille (aucun mouvement)"),
                    status_lbl.setStyleSheet("color: #94a3b8; font-weight: bold;"),
                    props.update({"motion_detected": False}),
                    self.property_changed.emit(comp_id, props)
                ))

            trigger_btn.clicked.connect(on_trigger)
            self.form_layout.addRow("Simulation :", trigger_btn)

        elif comp_type in ("joystick", "thumbstick"):
            x_val = int(props.get("x", 2048))
            y_val = int(props.get("y", 2048))

            x_slider = QSlider(Qt.Horizontal)
            x_slider.setRange(0, 4095)
            x_slider.setValue(x_val)
            x_lbl = QLabel(f"{x_val} ({x_val*3.3/4095:.2f}V)")
            x_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")

            def on_x_change(v):
                x_lbl.setText(f"{v} ({v*3.3/4095:.2f}V)")
                props["x"] = v
                self.property_changed.emit(comp_id, props)

            x_slider.valueChanged.connect(on_x_change)
            x_box = QHBoxLayout()
            x_box.addWidget(x_slider)
            x_box.addWidget(x_lbl)
            self.form_layout.addRow("Axe X (VRx) :", x_box)

            y_slider = QSlider(Qt.Horizontal)
            y_slider.setRange(0, 4095)
            y_slider.setValue(y_val)
            y_lbl = QLabel(f"{y_val} ({y_val*3.3/4095:.2f}V)")
            y_lbl.setStyleSheet("color: #38bdf8; font-weight: bold;")

            def on_y_change(v):
                y_lbl.setText(f"{v} ({v*3.3/4095:.2f}V)")
                props["y"] = v
                self.property_changed.emit(comp_id, props)

            y_slider.valueChanged.connect(on_y_change)
            y_box = QHBoxLayout()
            y_box.addWidget(y_slider)
            y_box.addWidget(y_lbl)
            self.form_layout.addRow("Axe Y (VRy) :", y_box)

        elif comp_type in ("switch", "slide_switch"):
            is_on = bool(props.get("is_on", False))
            toggle_btn = QPushButton("Position : ON (Droite)" if is_on else "Position : OFF (Gauche)")
            toggle_btn.setCheckable(True)
            toggle_btn.setChecked(is_on)
            toggle_btn.setCursor(Qt.PointingHandCursor)
            toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #334155;
                    color: #f8fafc;
                    border: 1px solid #475569;
                    border-radius: 4px;
                    padding: 6px;
                    font-weight: 600;
                }
                QPushButton:checked {
                    background-color: #16a34a;
                    color: white;
                }
            """)

            def on_toggle(checked):
                toggle_btn.setText("Position : ON (Droite)" if checked else "Position : OFF (Gauche)")
                props["is_on"] = checked
                self.property_changed.emit(comp_id, props)

            toggle_btn.toggled.connect(on_toggle)
            self.form_layout.addRow("État :", toggle_btn)

    def clear_selection(self):
        self.current_component_id = None
        self.current_component_type = None
        while self.form_layout.rowCount() > 0:
            self.form_layout.removeRow(0)
        self.title_label.setText("⚙ Propriétés")
        self.empty_label.setVisible(True)
