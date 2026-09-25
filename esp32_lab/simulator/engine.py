"""
Moteur principal de simulation (SimulationEngine)
"""

from PySide6.QtCore import QObject, Signal

from ..app.event_bus import get_event_bus
from .gpio import GPIOManager
from .adc import ADCManager
from .pwm import PWMManager
from .i2c import I2CManager
from .spi import SPIManager
from .runtime import MicroPythonRuntime


class SimulationEngine(QObject):
    def __init__(self):
        super().__init__()
        self.gpio_manager = GPIOManager()
        self.adc_manager = ADCManager(self.gpio_manager)
        self.pwm_manager = PWMManager(self.gpio_manager)
        self.i2c_manager = I2CManager()
        self.spi_manager = SPIManager(self.gpio_manager)
        self.runtime = MicroPythonRuntime(self.gpio_manager)

        # Phase 5.11/5.12 — Shared RuntimeCallbackQueue (IRQ + Timer unified)
        from .callback_queue import RuntimeCallbackQueue
        self.callback_queue = RuntimeCallbackQueue()

        # Phase 5.11 — GPIO Interrupt Controller (now uses shared queue)
        from .interrupts import InterruptController
        self.irq_controller = InterruptController(self.callback_queue)
        # Register as the first GPIO listener so it receives every state change
        self.gpio_manager.add_listener(self.irq_controller.on_gpio_changed)

        # Phase 5.12 — Timer Manager (uses same shared queue)
        from .timers import TimerManager
        self.timer_manager = TimerManager(self.callback_queue)

        # Phase 5.13 — UART Manager
        from .uart import UARTManager
        self.uart_manager = UARTManager(self.gpio_manager)

        # Inject managers into machine module
        from .modules import machine as sim_machine
        sim_machine.Pin._gpio_manager = self.gpio_manager
        sim_machine.Pin._irq_controller = self.irq_controller
        sim_machine.ADC.set_adc_manager(self.adc_manager)
        sim_machine.PWM.set_pwm_manager(self.pwm_manager)
        sim_machine.I2C.set_i2c_manager(self.i2c_manager)
        sim_machine.SPI.set_spi_manager(self.spi_manager)
        sim_machine.Timer._timer_manager = self.timer_manager
        sim_machine.UART._uart_manager = self.uart_manager

        self.event_bus = get_event_bus()

        self.event_bus.topology_updated.connect(self._on_topology_updated)

        # Connecter les notifications GPIO, PWM et ADC à l'EventBus
        self.gpio_manager.add_listener(self._on_gpio_changed)
        self.gpio_manager.add_pwm_listener(self._on_pwm_changed)
        self.gpio_manager.add_adc_listener(self._on_adc_changed)

        # Connecter les sorties du runtime à l'EventBus
        self.runtime.output_received.connect(self.event_bus.serial_data_received)
        self.runtime.error_occurred.connect(self.event_bus.simulation_error)
        self.runtime.simulation_started.connect(self.event_bus.simulation_started)
        self.runtime.simulation_finished.connect(self.event_bus.simulation_stopped)

        # Écouter les requêtes de l'UI via l'EventBus
        self.event_bus.request_simulation_stop.connect(self.stop)
        self.event_bus.request_simulation_reset.connect(self.reset)

    def _on_gpio_changed(self, pin: int, value: int):
        self.event_bus.gpio_changed.emit(pin, value)

    def _on_pwm_changed(self, pin: int, freq: int, duty: int):
        self.event_bus.pwm_changed.emit(pin, freq, duty)

    def _on_adc_changed(self, pin: int, value: int):
        self.event_bus.analog_changed.emit(pin, value)

    def _on_topology_updated(self, resolver, device_models):
        self.adc_manager.net_resolver = resolver
        self.adc_manager.device_models = device_models
        self.pwm_manager.net_resolver = resolver
        self.pwm_manager.device_models = device_models
        self.gpio_manager.net_resolver = resolver
        self.gpio_manager.device_models = device_models
        self.i2c_manager.net_resolver = resolver
        self.i2c_manager.device_models = device_models
        self.spi_manager.net_resolver = resolver
        self.spi_manager.device_models = device_models
        self.uart_manager.net_resolver = resolver
        self.uart_manager.device_models = device_models

        # Inject resolver and managers into models that need it
        for dev in device_models.values():
            if hasattr(dev, "set_net_resolver"):
                dev.set_net_resolver(resolver)
            if hasattr(dev, "_uart_manager"):
                dev._uart_manager = self.uart_manager

        # Turn off all devices on topology change to prevent zombie states
        for dev in device_models.values():
            if hasattr(dev, "set_pwm"):
                dev.set_pwm(1000, 0.0)

        # Trigger PWM update on all active pins to update newly connected devices
        for pin in list(self.pwm_manager._states.keys()):
            self.pwm_manager._update_devices(pin)

        # Phase 5.11: Re-evaluate IRQ baseline for INPUT pins after topology change.
        self._re_evaluate_input_irq_states()

    def _re_evaluate_input_irq_states(self):
        """
        After a topology update, re-read each INPUT pin that has an IRQ registered
        and push a synthetic notify if its resolved value changed.
        """
        from .gpio import GPIOMode
        for pin_id in list(self.irq_controller._registrations.keys()):
            mode = self.gpio_manager._modes.get(pin_id)
            if mode == GPIOMode.IN:
                resolved_val = self.gpio_manager.read(pin_id)
                old_val = self.irq_controller._prev_states.get(pin_id)
                if old_val is None:
                    self.irq_controller._prev_states[pin_id] = resolved_val
                elif old_val != resolved_val:
                    self.gpio_manager._notify(pin_id, resolved_val)
                    self.gpio_manager._values[pin_id] = resolved_val

    def start(self, code: str):
        self.event_bus.serial_data_received.emit(">>> [SIMULATION DÉMARRÉE]\n")
        self.runtime.start(code)

    def stop(self):
        if self.runtime.is_running():
            self.runtime.stop()

    def reset(self):
        self.stop()
        self.gpio_manager.reset()
        self.adc_manager.reset()
        self.pwm_manager.reset()
        self.i2c_manager.reset()
        self.spi_manager.reset()
        self.uart_manager.reset()
        # Phase 5.11: clear all IRQ registrations and pending state
        self.irq_controller.reset()
        # Phase 5.12: stop all timers
        self.timer_manager.reset()
        # Clear shared callback queue
        self.callback_queue.clear()
        self.event_bus.serial_data_received.emit(">>> [SIMULATION RÉINITIALISÉE]\n")

    def is_running(self) -> bool:
        return self.runtime.is_running()
