"""
Runtime d'exécution sécurisé et non-bloquant pour le code MicroPython utilisateur
"""

import ast
import io
import sys
import traceback
from typing import Callable
from PySide6.QtCore import QObject, QThread, Signal

from .gpio import GPIOManager
from .modules import machine as sim_machine
from .modules import time as sim_time


class SimulationWorker(QObject):
    """Worker Qt exécuté dans un QThread dédié"""
    output_received = Signal(str)
    error_occurred = Signal(str, int)  # message, line_number
    finished = Signal()

    def __init__(self, code: str, gpio_manager: GPIOManager):
        super().__init__()
        self.code = code
        self.gpio_manager = gpio_manager
        self._is_running = True

    def stop(self):
        self._is_running = False

    def is_stopped(self) -> bool:
        return not self._is_running

    def run(self):
        # Configurer le stop callback pour sim_time.sleep
        sim_time.set_stop_check_callback(self.is_stopped)
        sim_machine.Pin.set_gpio_manager(self.gpio_manager)

        # Vérification préliminaire de la syntaxe Python et sécurité AST
        try:
            tree = ast.parse(self.code, "main.py", "exec")
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr in ('__class__', '__bases__', '__subclasses__', '__globals__', '__builtins__', '__dict__'):
                    e = SyntaxError(f"Accès refusé à l'attribut sécurisé : {node.attr}")
                    e.lineno = getattr(node, 'lineno', 1)
                    raise e
            compile(tree, "main.py", "exec")
        except SyntaxError as se:
            line_no = se.lineno or 1
            err_msg = f"SyntaxError: {se.msg} (Ligne {line_no})"
            self.output_received.emit(f"❌ {err_msg}\n")
            self.error_occurred.emit(err_msg, line_no)
            self.finished.emit()
            return
        except Exception as ex:
            self.output_received.emit(f"❌ Erreur de compilation: {ex}\n")
            self.error_occurred.emit(str(ex), 1)
            self.finished.emit()
            return

        # Redirection de stdout pour intercepter print(...)
        class OutputRedirector(io.StringIO):
            def __init__(self, callback: Callable[[str], None]):
                super().__init__()
                self.callback = callback

            def write(self, s: str) -> int:
                if s:
                    self.callback(s)
                return len(s)

        old_stdout = sys.stdout
        old_stderr = sys.stderr
        redirector = OutputRedirector(self.output_received.emit)
        sys.stdout = redirector
        sys.stderr = redirector

        from .modules import dht as sim_dht
        from .modules import hcsr04 as sim_hcsr04
        from .modules import liquidcrystal_i2c as sim_lcd
        from .modules import neopixel as sim_neopixel
        from .modules import network as sim_network
        from .modules import mpu6050 as sim_mpu6050
        from .modules import tm1637 as sim_tm1637
        from .modules import bluetooth as sim_bluetooth
        from .modules import urequests as sim_urequests

        def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "machine":
                return sim_machine
            elif name == "time":
                return sim_time
            elif name == "dht":
                return sim_dht
            elif name == "hcsr04":
                return sim_hcsr04
            elif name in ("liquidcrystal_i2c", "lcd_api"):
                return sim_lcd
            elif name == "neopixel":
                return sim_neopixel
            elif name == "network":
                return sim_network
            elif name in ("bluetooth", "ubluetooth"):
                return sim_bluetooth
            elif name in ("urequests", "requests"):
                return sim_urequests
            elif name == "umqtt":
                from .modules import umqtt as sim_umqtt
                return sim_umqtt
            elif name == "umqtt.simple":
                from .modules.umqtt import simple as sim_umqtt_simple
                return sim_umqtt_simple
            elif name == "bme280":
                return sim_bme280
            elif name in ("mpu6050", "mpu_6050"):
                return sim_mpu6050
            elif name == "tm1637":
                return sim_tm1637
            elif name == "ssd1306":
                from .modules import ssd1306 as sim_ssd1306
                return sim_ssd1306
            elif name in ("socket", "usocket"):
                import socket
                return socket
            elif name == "micropython":
                import types
                mod = types.ModuleType("micropython")
                mod.const = lambda x: x
                mod.mem_info = lambda verbose=False: print("stack: 736/15360\nGC: total: 111168, used: 21856, free: 89312")
                mod.qstr_info = lambda verbose=False: print("qstr pool: n_pool=1, n_qstr=100")
                mod.alloc_emergency_exception_buf = lambda size: None
                mod.schedule = lambda func, arg: func(arg)
                mod.opt_level = lambda level=None: 0
                return mod
            elif name in ("math", "random", "json", "ujson", "struct", "ustruct"):
                import importlib
                mod_name = name.lstrip("u") if name.startswith("u") else name
                try:
                    return importlib.import_module(mod_name)
                except ImportError:
                    return importlib.import_module(name)
            raise ImportError(f"Le module '{name}' n'est pas disponible dans le simulateur ESP32.")
        def _check_attr(attr: str):
            if attr in ('__class__', '__bases__', '__subclasses__', '__globals__', '__builtins__', '__dict__'):
                raise AttributeError(f"Accès refusé à l'attribut sécurisé : {attr}")

        def safe_getattr(obj, name, *args):
            _check_attr(name)
            return getattr(obj, name, *args)

        def safe_setattr(obj, name, value):
            _check_attr(name)
            return setattr(obj, name, value)

        def safe_hasattr(obj, name):
            try:
                _check_attr(name)
            except AttributeError:
                return False
            return hasattr(obj, name)

        # Construction du namespace isolé
        sim_env = {
            "__name__": "__main__",
            "__builtins__": {
                "__import__": custom_import,
                "print": print,
                "range": range,
                "len": len,
                "int": int,
                "float": float,
                "str": str,
                "bool": bool,
                "list": list,
                "dict": dict,
                "set": set,
                "tuple": tuple,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "abs": abs,
                "min": min,
                "max": max,
                "round": round,
                "sum": sum,
                "sorted": sorted,
                "bytes": bytes,
                "bytearray": bytearray,
                "ord": ord,
                "chr": chr,
                "isinstance": isinstance,
                "hasattr": safe_hasattr,
                "getattr": safe_getattr,
                "setattr": safe_setattr,
                "all": all,
                "any": any,
                "bin": bin,
                "hex": hex,
                "oct": oct,
                "pow": pow,
                "True": True,
                "False": False,
                "None": None,
                "Exception": Exception,
                "KeyboardInterrupt": KeyboardInterrupt,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "IndexError": IndexError,
                "KeyError": KeyError,
                "ImportError": ImportError,
                "OSError": OSError,
                "RuntimeError": RuntimeError,
                "StopIteration": StopIteration,
                "AttributeError": AttributeError,
                "ZeroDivisionError": ZeroDivisionError,
                "__build_class__": __builtins__["__build_class__"],
            },
            "machine": sim_machine,
            "Pin": sim_machine.Pin,
            "PWM": sim_machine.PWM,
            "ADC": sim_machine.ADC,
            "I2C": sim_machine.I2C,
            "SPI": sim_machine.SPI,
            "UART": sim_machine.UART,
            "Timer": sim_machine.Timer,
            "dht": sim_dht,
            "time": sim_time,
            "sleep": sim_time.sleep,
            "sleep_ms": sim_time.sleep_ms,
        }

        # Hook de traçage pour stopper les boucles sans sleep (ex: while True: pass)
        # Also drains queued GPIO IRQ callbacks (Phase 5.11) and Timer callbacks
        # (Phase 5.12) between user code lines via the shared RuntimeCallbackQueue.
        def trace_lines(frame, event, arg):
            if not self._is_running:
                raise InterruptedError("Simulation arrêtée.")
            # Drain shared callback queue (IRQ + Timer) safely in sandbox thread
            irq_ctrl = getattr(sim_machine.Pin, '_irq_controller', None)
            if irq_ctrl is not None:
                irq_ctrl._queue.drain()
            return trace_lines

        sys.settrace(trace_lines)

        try:
            exec(self.code, sim_env)
            self.output_received.emit("\n>>> Programme terminé avec succès.\n")
        except InterruptedError:
            self.output_received.emit("\n>>> Simulation arrêtée par l'utilisateur.\n")
        except Exception as ex:
            tb = traceback.extract_tb(sys.exc_info()[2])
            # Chercher la dernière ligne dans main.py
            target_line = 1
            for frame in reversed(tb):
                if frame.filename in ("main.py", "<string>"):
                    target_line = frame.lineno or 1
                    break
            err_line_msg = f"❌ {type(ex).__name__} (Ligne {target_line}): {ex}\n"
            self.output_received.emit(err_line_msg)
            self.error_occurred.emit(str(ex), target_line)
        finally:
            sys.settrace(None)
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            self.finished.emit()


class MicroPythonRuntime(QObject):
    """Contrôleur de haut niveau du runtime MicroPython"""
    output_received = Signal(str)
    error_occurred = Signal(str, int)
    simulation_started = Signal()
    simulation_finished = Signal()

    def __init__(self, gpio_manager: GPIOManager):
        super().__init__()
        self.gpio_manager = gpio_manager
        self._thread: QThread | None = None
        self._worker: SimulationWorker | None = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def start(self, code: str):
        if self.is_running():
            self.stop()

        self._thread = QThread()
        self._worker = SimulationWorker(code, self.gpio_manager)
        self._worker.moveToThread(self._thread)

        self._worker.output_received.connect(self.output_received)
        self._worker.error_occurred.connect(self.error_occurred)
        self._worker.finished.connect(self._on_worker_finished)

        self._thread.started.connect(self._worker.run)
        self._thread.start()
        self.simulation_started.emit()

    def stop(self):
        if self._worker:
            self._worker.stop()
        if self._thread:
            self._thread.quit()
            if not self._thread.wait(600):
                self._thread.terminate()
                self._thread.wait(400)
            self._thread = None
            self._worker = None
        self.simulation_finished.emit()

    def _on_worker_finished(self):
        self.stop()
