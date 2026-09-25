"""
Panneau REPL MicroPython interactif (REPLPanelWidget)
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...app.event_bus import get_event_bus


class REPLPanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_bus = get_event_bus()
        self.history: list[str] = []
        self.history_index: int = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # En-tête REPL compact
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        self.title_label = QLabel("📟 REPL")
        self.title_label.setObjectName("REPLTitle")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.btn_reset = QPushButton("↻ Reset")
        self.btn_reset.setToolTip("Effectuer un redémarrage logiciel (Ctrl+D)")
        self.btn_reset.clicked.connect(self._soft_reset)
        header_layout.addWidget(self.btn_reset)

        self.btn_interrupt = QPushButton("⏹ Stop")
        self.btn_interrupt.setToolTip("Envoyer KeyboardInterrupt (Ctrl+C)")
        self.btn_interrupt.clicked.connect(self._interrupt)
        header_layout.addWidget(self.btn_interrupt)

        layout.addLayout(header_layout)

        # Terminal text display
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.terminal.setFont(font)
        self._show_banner()
        layout.addWidget(self.terminal)

        # Ligne de saisie interactive
        input_layout = QHBoxLayout()
        self.prompt_label = QLabel(">>>")
        input_layout.addWidget(self.prompt_label)

        self.repl_input = QLineEdit()
        self.repl_input.setPlaceholderText("help() ou commande Python...")
        self.repl_input.setFont(font)
        self.repl_input.returnPressed.connect(self._execute_command)
        input_layout.addWidget(self.repl_input)

        layout.addLayout(input_layout)

        self.set_theme("dark")

        # Connexion unique (ne PAS mettre dans set_theme !)
        self.event_bus.repl_data_received.connect(self.append_output)

    def set_theme(self, theme_name: str):
        """Adapte les couleurs du REPL selon le thème."""
        is_light = (theme_name == "light")
        title_col = "#0f172a" if is_light else "#f8fafc"
        self.title_label.setStyleSheet(f"font-weight: 700; color: {title_col}; font-size: 11px;")

        btn_bg = "#e2e8f0" if is_light else "#1e293b"
        btn_fg = "#0f172a" if is_light else "#f8fafc"
        btn_border = "#cbd5e1" if is_light else "#334155"
        btn_style = f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_fg};
                border: 1px solid {btn_border};
                border-radius: 4px;
                font-size: 11px;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background-color: #cbd5e1;
            }}
        """ if is_light else f"""
            QPushButton {{
                background-color: {btn_bg};
                color: {btn_fg};
                border: 1px solid {btn_border};
                border-radius: 4px;
                font-size: 11px;
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background-color: #334155;
            }}
        """
        self.btn_reset.setStyleSheet(btn_style)
        self.btn_interrupt.setStyleSheet(btn_style)

        term_bg = "#f8fafc" if is_light else "#080c14"
        term_fg = "#047857" if is_light else "#10b981" # Vert émeraude profond / vert fluo
        term_border = "#cbd5e1" if is_light else "#1e293b"
        self.terminal.setStyleSheet(f"""
            background-color: {term_bg};
            color: {term_fg};
            border: 1px solid {term_border};
            border-radius: 6px;
            padding: 6px;
        """)

        prompt_col = "#047857" if is_light else "#10b981"
        self.prompt_label.setStyleSheet(f"color: {prompt_col}; font-family: Consolas; font-weight: bold; font-size: 13px;")

        inp_bg = "#ffffff" if is_light else "#0f172a"
        inp_fg = "#0f172a" if is_light else "#f8fafc"
        inp_border = "#cbd5e1" if is_light else "#2a3449"
        self.repl_input.setStyleSheet(f"""
            background-color: {inp_bg};
            color: {inp_fg};
            border: 1px solid {inp_border};
            border-radius: 4px;
            padding: 4px 8px;
        """)


    def _show_banner(self):
        banner = (
            "MicroPython v1.22.2 sur ESP32 module with ESP32 (Environnement Lab)\n"
            "Tapez \"help()\" pour plus d'informations ou entrez du code directement.\n"
            ">>> \n"
        )
        self.terminal.setPlainText(banner)

    def append_output(self, text: str):
        self.terminal.moveCursor(QTextCursor.End)
        self.terminal.insertPlainText(text)
        self.terminal.moveCursor(QTextCursor.End)

    def _execute_command(self):
        cmd = self.repl_input.text()
        if not cmd:
            self.append_output(">>> \n")
            return

        self.history.append(cmd)
        self.history_index = len(self.history)
        self.append_output(f">>> {cmd}\n")
        self.repl_input.clear()

        # Émettre la commande REPL
        self.event_bus.repl_data_to_send.emit(cmd)

        # Évaluation locale simplifiée si non connecté à une carte physique
        if cmd == "help()":
            self.append_output(
                "Bienvenue dans ESP32 MicroPython Lab !\n"
                "Modules disponibles : machine (Pin, PWM, ADC), time (sleep, ticks_ms)\n"
                "Utilisez l'éditeur pour les programmes complets et lancez la simulation.\n"
                ">>> \n"
            )
        else:
            if not hasattr(self, "repl_env"):
                self.repl_env = {}
                try:
                    from esp32_lab.simulator.modules import machine as sim_machine
                    from esp32_lab.simulator.modules import time as sim_time
                    self.repl_env.update({
                        "machine": sim_machine,
                        "Pin": sim_machine.Pin,
                        "PWM": sim_machine.PWM,
                        "ADC": sim_machine.ADC,
                        "time": sim_time,
                        "sleep": sim_time.sleep,
                    })
                except Exception:
                    pass

            try:
                # Évaluation d'expression ou instruction
                res = eval(cmd, self.repl_env)
                if res is not None:
                    self.append_output(f"{res}\n>>> ")
                else:
                    self.append_output(">>> ")
            except Exception:
                try:
                    exec(cmd, self.repl_env)
                    self.append_output(">>> ")
                except Exception as ex:
                    self.append_output(f"{type(ex).__name__}: {ex}\n>>> ")

    def _soft_reset(self):
        self.append_output("\nMPY: soft reboot\n")
        self._show_banner()
        self.event_bus.request_simulation_reset.emit()

    def _interrupt(self):
        self.append_output("\nTraceback (most recent call last):\n  KeyboardInterrupt\n>>> ")
        self.event_bus.request_simulation_stop.emit()
