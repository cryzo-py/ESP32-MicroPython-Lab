"""
Oscilloscope Virtuel & Analyseur Logique Professionnel 4 Canaux (OscilloscopePanel)
Supporte 4 voies configurables individuellement (GPIO logique, signal PWM ou tension ADC 0-3.3V).
Comprend :
- Base de temps réglable (100 ms à 5.0 s).
- Sélecteur de broche d'écoute par voie (GPIO 2, 4, 5, 12-19, 21-23, etc. ou ADC 32-39).
- Mesure automatique : Fréquence (Hz), Rapport cyclique (Duty Cycle %), Tension crête-à-crête.
- Curseurs temporels de mesure (T1, T2, Δt et 1/Δt).
- Grille phosphorique de laboratoire et OSD télémétrique.
"""

import collections
import time
from PySide6.QtCore import QPointF, QRectF, QTimer, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from ...app.event_bus import get_event_bus


class OscilloscopeScreen(QWidget):
    """Écran de traçage multi-canaux avec grille phosphorique et curseurs."""

    CHANNEL_COLORS = [
        QColor("#facc15"),  # CH1 : Jaune ambre
        QColor("#38bdf8"),  # CH2 : Bleu cyan
        QColor("#4ade80"),  # CH3 : Vert émeraude
        QColor("#f472b6"),  # CH4 : Rose magenta
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)
        self.setStyleSheet("background-color: #03120e; border: 1px solid #064e3b; border-radius: 4px;")

        # 4 buffers d'échantillons temporels : (timestamp, valeur_flottante_0_a_1_ou_volts)
        self.channel_samples = [collections.deque(maxlen=1500) for _ in range(4)]
        self.channel_enabled = [True, True, True, True]
        self.channel_pins = [2, 4, 18, 34]  # Broches surveillées par défaut
        self.channel_is_adc = [False, False, False, True]

        self.is_running = True
        self.timebase_sec = 2.0  # Fenêtre temporelle par défaut : 2 secondes

        # Mesures dynamiques
        self.freq_hz = [0.0, 0.0, 0.0, 0.0]
        self.duty_percent = [0.0, 0.0, 0.0, 0.0]
        self.latest_vals = [0.0, 0.0, 0.0, 0.0]

        # Curseurs de mesure (positions normalisées 0.0 à 1.0)
        self.show_cursors = False
        self.cursor_t1 = 0.35
        self.cursor_t2 = 0.65
        self.dragging_cursor = None

    @property
    def ch1_samples(self):
        """Propriété rétrocompatible pour la voie 1."""
        return self.channel_samples[0]

    @property
    def ch2_samples(self):
        """Propriété rétrocompatible pour la voie 2."""
        return self.channel_samples[1]

    @property
    def latest_voltage(self) -> float:
        """Tension de la voie ADC (par défaut voie 2 ou 4)."""
        return self.latest_vals[1] if self.channel_is_adc[1] else self.latest_vals[3]

    def add_ch1_sample(self, val: int):
        """Méthode rétrocompatible pour injecter un échantillon sur voie 1."""
        self.add_sample(0, 1.0 if val else 0.0)

    def add_ch2_sample(self, voltage: float):
        """Méthode rétrocompatible pour injecter une tension sur voie 2."""
        self.channel_is_adc[1] = True
        self.add_sample(1, float(voltage))

    def add_sample(self, ch_idx: int, val: float):
        if self.is_running and 0 <= ch_idx < 4:
            now = time.time()
            self.latest_vals[ch_idx] = float(val)
            self.channel_samples[ch_idx].append((now, float(val)))

    def clear_screen(self):
        for buf in self.channel_samples:
            buf.clear()
        self.update()

    def mousePressEvent(self, event):
        if not self.show_cursors:
            return
        w = self.width()
        x = event.position().x()
        x1 = self.cursor_t1 * w
        x2 = self.cursor_t2 * w
        if abs(x - x1) < 12:
            self.dragging_cursor = 1
        elif abs(x - x2) < 12:
            self.dragging_cursor = 2

    def mouseMoveEvent(self, event):
        if not self.show_cursors or not self.dragging_cursor:
            return
        w = max(1, self.width())
        norm = max(0.0, min(1.0, event.position().x() / w))
        if self.dragging_cursor == 1:
            self.cursor_t1 = norm
        elif self.dragging_cursor == 2:
            self.cursor_t2 = norm
        self.update()

    def mouseReleaseEvent(self, event):
        self.dragging_cursor = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # 1. Grille d'oscilloscope 10x8 carreaux
        grid_pen = QPen(QColor("#063b2c"), 1, Qt.DotLine)
        painter.setPen(grid_pen)

        cols = 10
        rows = 8
        for c in range(1, cols):
            x = c * (w / cols)
            painter.drawLine(x, 0, x, h)
        for r in range(1, rows):
            y = r * (h / rows)
            painter.drawLine(0, y, w, y)

        now = time.time()
        t_start = now - self.timebase_sec

        # 2. Dessin des 4 canaux
        # Diviser l'écran en 4 pistes verticales équilibrées
        lane_height = h / 4.0

        for ch in range(4):
            if not self.channel_enabled[ch]:
                continue

            samples = self.channel_samples[ch]
            if len(samples) < 2:
                continue

            col = self.CHANNEL_COLORS[ch]
            painter.setPen(QPen(col, 2))
            path = QPainterPath()
            started = False

            y_base = lane_height * (ch + 1) - 6
            y_peak = lane_height * ch + 12

            prev_x = None
            prev_y = None

            is_adc = self.channel_is_adc[ch]

            for t, val in samples:
                if t < t_start:
                    continue
                x = ((t - t_start) / self.timebase_sec) * w

                if is_adc:
                    # Tension 0.0V à 3.3V
                    ratio = max(0.0, min(1.0, val / 3.3))
                    y = y_base - ratio * (y_base - y_peak)
                else:
                    # Signal logique 0 ou 1
                    y = y_peak if val >= 0.5 else y_base

                if not started:
                    path.moveTo(x, y)
                    started = True
                else:
                    if not is_adc and prev_y is not None and prev_y != y:
                        # Front vertical franc
                        path.lineTo(x, prev_y)
                    path.lineTo(x, y)

                prev_x = x
                prev_y = y

            if started and prev_x is not None and prev_y is not None:
                path.lineTo(w, prev_y)

            painter.drawPath(path)

        # 3. Curseurs temporels (T1 et T2) si activés
        if self.show_cursors:
            x1 = self.cursor_t1 * w
            x2 = self.cursor_t2 * w
            cur_pen = QPen(QColor("#e2e8f0"), 1, Qt.DashLine)
            painter.setPen(cur_pen)
            painter.drawLine(x1, 0, x1, h)
            painter.drawLine(x2, 0, x2, h)

            # Labels T1 / T2
            painter.setFont(QFont("Consolas", 8, QFont.Bold))
            painter.setPen(QColor("#f8fafc"))
            painter.drawText(int(x1) + 4, 18, "T1")
            painter.drawText(int(x2) + 4, 18, "T2")

            # Mesure delta t
            dt_sec = abs(self.cursor_t2 - self.cursor_t1) * self.timebase_sec
            freq_calc = (1.0 / dt_sec) if dt_sec > 1e-4 else 0.0
            dt_text = f"Δt = {dt_sec*1000.0:.1f} ms | 1/Δt = {freq_calc:.1f} Hz"
            painter.setPen(QColor("#38bdf8"))
            painter.drawText(w // 2 - 80, h - 8, dt_text)

        # 4. Télémétrie OSD (On-Screen Display)
        painter.setFont(QFont("Consolas", 8, QFont.Bold))
        for ch in range(4):
            if not self.channel_enabled[ch]:
                continue
            col = self.CHANNEL_COLORS[ch]
            painter.setPen(col)
            pin_label = f"GPIO {self.channel_pins[ch]}" if not self.channel_is_adc[ch] else f"ADC Pin {self.channel_pins[ch]}"
            val_txt = f"{self.latest_vals[ch]:.2f}V" if self.channel_is_adc[ch] else ("HIGH" if self.latest_vals[ch] >= 0.5 else "LOW")
            osd_str = f"CH{ch+1} [{pin_label}]: {val_txt}"
            if self.freq_hz[ch] > 0:
                osd_str += f" | {self.freq_hz[ch]:.1f}Hz ({self.duty_percent[ch]:.0f}%)"
            y_osd = int(lane_height * ch) + 14
            painter.drawText(8, y_osd, osd_str)

        # Indicateur Run/Hold
        painter.setPen(QColor("#22c55e" if self.is_running else "#ef4444"))
        painter.drawText(w - 55, 16, "RUN" if self.is_running else "HOLD")


class OscilloscopePanel(QFrame):
    """Panneau complet avec sélecteurs de broches et réglages de l'oscilloscope."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #0b1329;
                border-top: 1px solid #1e293b;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # 1. Barre d'outils supérieure
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self.title_label = QLabel("📊 Oscilloscope & Analyseur 4 Voies (DSO)")
        self.title_label.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px;")
        bar.addWidget(self.title_label)

        self.btn_run_hold = QPushButton("⏸ Hold")
        self.btn_run_hold.clicked.connect(self._toggle_run)
        bar.addWidget(self.btn_run_hold)

        self.btn_clear = QPushButton("🗑️ Effacer")
        self.btn_clear.clicked.connect(self._clear_screen)
        bar.addWidget(self.btn_clear)

        self.btn_cursors = QPushButton("📏 Curseurs Δt")
        self.btn_cursors.setCheckable(True)
        self.btn_cursors.clicked.connect(self._toggle_cursors)
        bar.addWidget(self.btn_cursors)

        bar.addStretch()

        self.lbl_timebase = QLabel("Base de temps :")
        self.lbl_timebase.setStyleSheet("color: #94a3b8; font-size: 11px;")
        bar.addWidget(self.lbl_timebase)

        self.combo_tb = QComboBox()
        self.combo_tb.addItems(["500 ms", "1.0 s", "2.0 s", "5.0 s", "250 ms", "100 ms"])
        self.combo_tb.setCurrentIndex(2)  # 2.0 s
        self.combo_tb.currentIndexChanged.connect(self._on_timebase_changed)
        bar.addWidget(self.combo_tb)

        layout.addLayout(bar)

        # 2. Écran graphique de tracé
        self.screen = OscilloscopeScreen(self)
        layout.addWidget(self.screen)

        # 3. Barre inférieure de configuration des 4 Voies (CH1 à CH4)
        channels_bar = QHBoxLayout()
        channels_bar.setSpacing(12)

        AVAILABLE_PINS = [
            ("GPIO 2 (LED)", 2, False),
            ("GPIO 4", 4, False),
            ("GPIO 5", 5, False),
            ("GPIO 12", 12, False),
            ("GPIO 13", 13, False),
            ("GPIO 14", 14, False),
            ("GPIO 15", 15, False),
            ("GPIO 18", 18, False),
            ("GPIO 19", 19, False),
            ("GPIO 21 (SDA)", 21, False),
            ("GPIO 22 (SCL)", 22, False),
            ("GPIO 23", 23, False),
            ("ADC Pin 32", 32, True),
            ("ADC Pin 34", 34, True),
            ("ADC Pin 35", 35, True),
            ("ADC Pin 36 (VP)", 36, True),
            ("ADC Pin 39 (VN)", 39, True),
        ]

        self.channel_combos = []
        self.channel_checks = []

        default_indices = [0, 1, 7, 13]  # GPIO 2, GPIO 4, GPIO 18, ADC 34

        for ch in range(4):
            ch_box = QHBoxLayout()
            ch_box.setSpacing(4)

            chk = QCheckBox(f"CH{ch+1}")
            chk.setChecked(True)
            col_hex = self.screen.CHANNEL_COLORS[ch].name()
            chk.setStyleSheet(f"color: {col_hex}; font-weight: bold; font-size: 11px;")
            chk.toggled.connect(lambda checked, idx=ch: self._on_channel_toggled(idx, checked))
            ch_box.addWidget(chk)
            self.channel_checks.append(chk)

            cmb = QComboBox()
            for label, pin_num, is_adc in AVAILABLE_PINS:
                cmb.addItem(label, (pin_num, is_adc))
            cmb.setCurrentIndex(default_indices[ch])
            cmb.setStyleSheet("""
                QComboBox {
                    background-color: #1e293b;
                    color: #f8fafc;
                    border: 1px solid #334155;
                    border-radius: 4px;
                    padding: 1px 4px;
                    font-size: 10px;
                }
            """)
            cmb.currentIndexChanged.connect(lambda c_idx, idx=ch: self._on_pin_selection_changed(idx, c_idx))
            ch_box.addWidget(cmb)
            self.channel_combos.append(cmb)

            channels_bar.addLayout(ch_box)

        channels_bar.addStretch()
        layout.addLayout(channels_bar)

        # Timer de rafraîchissement à 30 FPS
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.screen.update)
        self.refresh_timer.start(33)

        # Connexions EventBus
        event_bus = get_event_bus()
        event_bus.gpio_changed.connect(self._on_gpio_changed)
        event_bus.pwm_changed.connect(self._on_pwm_changed)
        event_bus.analog_changed.connect(self._on_analog_changed)
        event_bus.simulation_stopped.connect(self._on_sim_stopped)

        self.set_theme("dark")

    def _toggle_run(self):
        self.screen.is_running = not self.screen.is_running
        self.btn_run_hold.setText("▶ Reprendre" if not self.screen.is_running else "⏸ Hold")

    def _clear_screen(self):
        self.screen.clear_screen()

    def _toggle_cursors(self, enabled: bool):
        self.screen.show_cursors = enabled
        self.screen.update()

    def _on_timebase_changed(self, idx: int):
        val_sec = [0.5, 1.0, 2.0, 5.0, 0.25, 0.1][idx]
        self.screen.timebase_sec = val_sec

    def _on_channel_toggled(self, ch_idx: int, enabled: bool):
        self.screen.channel_enabled[ch_idx] = enabled
        self.screen.update()

    def _on_pin_selection_changed(self, ch_idx: int, combo_idx: int):
        cmb = self.channel_combos[ch_idx]
        data = cmb.itemData(combo_idx)
        if data:
            pin_num, is_adc = data
            self.screen.channel_pins[ch_idx] = pin_num
            self.screen.channel_is_adc[ch_idx] = is_adc
            self.screen.channel_samples[ch_idx].clear()

    def _on_gpio_changed(self, pin_num: int, val: int):
        for ch in range(4):
            if self.screen.channel_pins[ch] == pin_num and not self.screen.channel_is_adc[ch]:
                self.screen.add_sample(ch, 1.0 if val else 0.0)

    def _on_pwm_changed(self, pin_num: int, freq: int, duty: int):
        for ch in range(4):
            if self.screen.channel_pins[ch] == pin_num and not self.screen.channel_is_adc[ch]:
                self.screen.freq_hz[ch] = float(freq)
                self.screen.duty_percent[ch] = float(duty) / 1023.0 * 100.0 if duty <= 1023 else float(duty) / 255.0 * 100.0
                self.screen.add_sample(ch, 1.0 if duty > 0 else 0.0)

    def _on_analog_changed(self, pin_num: int, raw_val: int):
        # raw_val = 0-4095 -> 0.0V à 3.3V
        voltage = (float(raw_val) / 4095.0) * 3.3
        for ch in range(4):
            if self.screen.channel_pins[ch] == pin_num and self.screen.channel_is_adc[ch]:
                self.screen.add_sample(ch, voltage)

    def set_adc_voltage(self, voltage: float):
        """Méthode compatible avec l'ancienne signature."""
        for ch in range(4):
            if self.screen.channel_is_adc[ch]:
                self.screen.add_sample(ch, float(voltage))

    def _on_sim_stopped(self):
        for ch in range(4):
            self.screen.add_sample(ch, 0.0)

    def set_theme(self, theme_name: str):
        is_light = (theme_name == "light")
        btn_bg = "#e2e8f0" if is_light else "#1e293b"
        btn_fg = "#0f172a" if is_light else "#e2e8f0"
        btn_border = "#cbd5e1" if is_light else "#334155"
        btn_style = f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_fg};
                border: 1px solid {btn_border};
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background-color: {btn_border}; }}
            QPushButton:checked {{ background-color: #0284c7; color: white; }}
        """
        self.btn_run_hold.setStyleSheet(btn_style)
        self.btn_clear.setStyleSheet(btn_style)
        self.btn_cursors.setStyleSheet(btn_style)