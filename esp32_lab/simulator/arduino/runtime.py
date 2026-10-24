"""
Runtime Qt asynchrone pour l'exécution non-bloquante du code Arduino C / C++.
Offre la même interface et les mêmes signaux Qt que MicroPythonRuntime.
"""

from __future__ import annotations
import traceback
from typing import Optional
from PySide6.QtCore import QObject, QThread, Signal

from ..gpio import GPIOManager
from ..adc import ADCManager
from ..pwm import PWMManager
from .lexer import ArduinoLexer
from .parser import ArduinoParser
from .interpreter import (
    ArduinoInterpreter,
    ArduinoStopException,
    ArduinoRuntimeError
)


class ArduinoWorker(QObject):
    """Worker exécuté dans un QThread dédié pour ne pas bloquer l'interface graphique."""
    output_received = Signal(str)
    error_occurred = Signal(str, int)  # message, line_number
    finished = Signal()

    def __init__(
        self,
        code: str,
        gpio_manager: GPIOManager,
        adc_manager: Optional[ADCManager] = None,
        pwm_manager: Optional[PWMManager] = None,
        board_profile: Optional[Any] = None
    ):
        super().__init__()
        self.code = code
        self.gpio_manager = gpio_manager
        self.adc_manager = adc_manager
        self.pwm_manager = pwm_manager
        self.board_profile = board_profile
        self._is_running = True
        self.interpreter: Optional[ArduinoInterpreter] = None

    def stop(self):
        self._is_running = False

    def is_stopped(self) -> bool:
        return not self._is_running

    def run(self):
        try:
            # 1. Analyse lexicale et prétraitement
            lexer = ArduinoLexer(self.code)
            tokens = lexer.tokenize()

            # 2. Analyse syntaxique (Parsing AST)
            parser = ArduinoParser(tokens)
            program = parser.parse()

            # 3. Interprétation et exécution du sketch
            self.interpreter = ArduinoInterpreter(
                gpio_manager=self.gpio_manager,
                adc_manager=self.adc_manager,
                pwm_manager=self.pwm_manager,
                board_profile=self.board_profile,
                output_callback=self.output_received.emit,
                stop_check=self.is_stopped
            )
            self.interpreter.run(program)

        except SyntaxError as se:
            line_no = getattr(se, 'lineno', None)
            if line_no is None:
                # Tenter d'extraire la ligne du message
                import re
                m = re.search(r'ligne\s+(\d+)', str(se), re.IGNORECASE)
                line_no = int(m.group(1)) if m else 1
            err_msg = f"Erreur de syntaxe Arduino C++: {se}"
            self.output_received.emit(f"❌ {err_msg}\n")
            self.error_occurred.emit(err_msg, line_no)

        except ArduinoRuntimeError as are:
            err_msg = f"Erreur d'exécution: {are.message} (Ligne {are.line})"
            self.output_received.emit(f"❌ {err_msg}\n")
            self.error_occurred.emit(err_msg, are.line)

        except ArduinoStopException:
            # Arrêt normal demandé par l'utilisateur
            pass

        except Exception as ex:
            err_msg = f"Erreur inattendue: {ex}"
            self.output_received.emit(f"❌ {err_msg}\n")
            self.error_occurred.emit(err_msg, 1)

        finally:
            self.finished.emit()


class ArduinoRuntime(QObject):
    """Contrôleur de haut niveau gérant le thread d'exécution Arduino."""
    output_received = Signal(str)
    error_occurred = Signal(str, int)
    simulation_started = Signal()
    simulation_finished = Signal()

    def __init__(
        self,
        gpio_manager: GPIOManager,
        adc_manager: Optional[ADCManager] = None,
        pwm_manager: Optional[PWMManager] = None,
        board_profile: Optional[Any] = None
    ):
        super().__init__()
        self.gpio_manager = gpio_manager
        self.adc_manager = adc_manager
        self.pwm_manager = pwm_manager
        self.board_profile = board_profile or getattr(gpio_manager, "board_profile", None)
        self.thread: Optional[QThread] = None
        self.worker: Optional[ArduinoWorker] = None

    def set_board_profile(self, profile: Any):
        """Met à jour le profil de carte actif."""
        self.board_profile = profile
        if self.worker and self.worker.interpreter:
            self.worker.interpreter.set_board_profile(profile)

    def is_running(self) -> bool:
        return self.thread is not None and self.thread.isRunning()

    def start(self, code: str):
        """Lance l'exécution du code Arduino dans un thread d'arrière-plan."""
        if self.is_running():
            self.stop()

        self.thread = QThread()
        self.worker = ArduinoWorker(
            code=code,
            gpio_manager=self.gpio_manager,
            adc_manager=self.adc_manager,
            pwm_manager=self.pwm_manager,
            board_profile=self.board_profile
        )
        self.worker.moveToThread(self.thread)

        self.worker.output_received.connect(self.output_received.emit)
        self.worker.error_occurred.connect(self.error_occurred.emit)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self._on_finished)

        self.thread.start()
        self.simulation_started.emit()

    def stop(self):
        """Arrête immédiatement l'exécution en cours."""
        if self.worker:
            self.worker.stop()
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait(600)
        self.thread = None
        self.worker = None

    def _on_finished(self):
        self.simulation_finished.emit()
