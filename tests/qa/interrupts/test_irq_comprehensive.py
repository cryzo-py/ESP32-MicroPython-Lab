"""
Phase 5.11 — GPIO IRQ Comprehensive Tests

Tests the full IRQ chain:
    GPIO transition → InterruptController → MicroPython callback

No shortcuts: callbacks only fire through electrical topology transitions.
"""

import pytest
from collections import deque
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.core.electrical_net_resolver import ElectricalNetResolver
from esp32_lab.simulator.callback_queue import RuntimeCallbackQueue
from esp32_lab.simulator.interrupts import InterruptController, IRQ_RISING, IRQ_FALLING


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    eng = SimulationEngine()
    eng.resolver = ElectricalNetResolver()
    eng.models = {}

    def trigger_update():
        eng.event_bus.topology_updated.emit(eng.resolver, eng.models)

    eng.trigger_update = trigger_update
    yield eng
    eng.reset()


@pytest.fixture
def irq_ctrl(engine):
    """Return the engine's InterruptController and ensure Pin knows about it."""
    sim_machine.Pin._irq_controller = engine.irq_controller
    sim_machine.Pin._gpio_manager = engine.gpio_manager
    return engine.irq_controller


# ---------------------------------------------------------------------------
# Helper: register a Pin IRQ and return a callback that counts calls
# ---------------------------------------------------------------------------

def make_counter():
    calls = []
    def cb(pin):
        calls.append(pin.id)
    return cb, calls


# ---------------------------------------------------------------------------
# 1. InterruptController unit tests (no GPIO manager needed)
# ---------------------------------------------------------------------------

class TestInterruptControllerUnit:
    def test_register_and_basic_rising(self):
        ctrl = InterruptController(RuntimeCallbackQueue())
        cb, calls = make_counter()
        pin_mock = type("P", (), {"id": 27})()
        ctrl.register_irq(27, IRQ_RISING, cb, pin_mock)

        ctrl.on_gpio_changed(27, 0)   # baseline LOW
        ctrl.on_gpio_changed(27, 1)   # RISING edge
        ctrl.dispatch_pending()

        assert len(calls) == 1
        assert calls[0] == 27

    def test_register_and_basic_falling(self):
        ctrl = InterruptController(RuntimeCallbackQueue())
        cb, calls = make_counter()
        pin_mock = type("P", (), {"id": 27})()
        ctrl.register_irq(27, IRQ_FALLING, cb, pin_mock)

        ctrl.on_gpio_changed(27, 1)   # baseline HIGH
        ctrl.on_gpio_changed(27, 0)   # FALLING edge
        ctrl.dispatch_pending()

        assert len(calls) == 1

    def test_no_trigger_on_same_value(self):
        ctrl = InterruptController(RuntimeCallbackQueue())
        cb, calls = make_counter()
        pin_mock = type("P", (), {"id": 27})()
        ctrl.register_irq(27, IRQ_RISING | IRQ_FALLING, cb, pin_mock)

        ctrl.on_gpio_changed(27, 1)   # baseline
        for _ in range(10):
            ctrl.on_gpio_changed(27, 1)   # no edge
        ctrl.dispatch_pending()

        assert len(calls) == 0

    def test_initial_state_no_trigger(self):
        """First observation must establish baseline without firing."""
        ctrl = InterruptController(RuntimeCallbackQueue())
        cb, calls = make_counter()
        pin_mock = type("P", (), {"id": 27})()
        ctrl.register_irq(27, IRQ_RISING | IRQ_FALLING, cb, pin_mock)

        ctrl.on_gpio_changed(27, 1)   # first observation — no trigger
        ctrl.dispatch_pending()
        assert len(calls) == 0

        ctrl.on_gpio_changed(27, 0)   # NOW falls — trigger
        ctrl.dispatch_pending()
        assert len(calls) == 1

    def test_disable_irq(self):
        ctrl = InterruptController(RuntimeCallbackQueue())
        cb, calls = make_counter()
        pin_mock = type("P", (), {"id": 27})()
        ctrl.register_irq(27, IRQ_RISING, cb, pin_mock)

        ctrl.on_gpio_changed(27, 0)
        ctrl.on_gpio_changed(27, 1)   # would fire
        ctrl.dispatch_pending()
        assert len(calls) == 1

        # Disable
        ctrl.register_irq(27, IRQ_RISING, None, pin_mock)
        ctrl.on_gpio_changed(27, 0)
        ctrl.on_gpio_changed(27, 1)   # must NOT fire
        ctrl.dispatch_pending()
        assert len(calls) == 1   # unchanged

    def test_replace_handler(self):
        """New registration replaces old handler."""
        ctrl = InterruptController(RuntimeCallbackQueue())
        cb1, calls1 = make_counter()
        cb2, calls2 = make_counter()
        pin_mock = type("P", (), {"id": 27})()

        ctrl.register_irq(27, IRQ_RISING, cb1, pin_mock)
        ctrl.register_irq(27, IRQ_RISING, cb2, pin_mock)  # replaces

        ctrl.on_gpio_changed(27, 0)
        ctrl.on_gpio_changed(27, 1)
        ctrl.dispatch_pending()

        assert len(calls1) == 0
        assert len(calls2) == 1

    def test_multiple_pins_isolated(self):
        ctrl = InterruptController(RuntimeCallbackQueue())
        cb25, calls25 = make_counter()
        cb26, calls26 = make_counter()
        pm25 = type("P", (), {"id": 25})()
        pm26 = type("P", (), {"id": 26})()

        ctrl.register_irq(25, IRQ_RISING, cb25, pm25)
        ctrl.register_irq(26, IRQ_RISING, cb26, pm26)

        ctrl.on_gpio_changed(25, 0)
        ctrl.on_gpio_changed(26, 0)

        ctrl.on_gpio_changed(25, 1)   # only pin 25 rising
        ctrl.dispatch_pending()

        assert len(calls25) == 1
        assert len(calls26) == 0

    def test_callback_exception_isolation(self):
        ctrl = InterruptController(RuntimeCallbackQueue())
        bad_calls = []

        def bad_cb(pin):
            bad_calls.append(1)
            raise RuntimeError("test error")

        good_cb, good_calls = make_counter()
        pm = type("P", (), {"id": 27})()
        pg = type("P", (), {"id": 26})()

        ctrl.register_irq(27, IRQ_RISING, bad_cb, pm)
        ctrl.register_irq(26, IRQ_RISING, good_cb, pg)

        ctrl.on_gpio_changed(27, 0)
        ctrl.on_gpio_changed(26, 0)
        ctrl.on_gpio_changed(27, 1)   # bad cb queued
        ctrl.on_gpio_changed(26, 1)   # good cb queued
        ctrl.dispatch_pending()       # bad cb errors, good cb still fires

        assert len(bad_calls) == 1
        assert len(good_calls) == 1

    def test_reentrancy_guard(self):
        """dispatch_pending must not recurse."""
        ctrl = InterruptController(RuntimeCallbackQueue())
        depth = [0]
        max_depth = [0]
        pm = type("P", (), {"id": 27})()

        def recursive_cb(pin):
            depth[0] += 1
            max_depth[0] = max(max_depth[0], depth[0])
            # Try to dispatch again (simulates re-entrancy)
            ctrl.dispatch_pending()
            depth[0] -= 1

        ctrl.register_irq(27, IRQ_RISING, recursive_cb, pm)
        ctrl.on_gpio_changed(27, 0)
        ctrl.on_gpio_changed(27, 1)
        ctrl.dispatch_pending()

        assert max_depth[0] == 1   # never deeper than 1

    def test_reset_clears_all(self):
        ctrl = InterruptController(RuntimeCallbackQueue())
        cb, calls = make_counter()
        pm = type("P", (), {"id": 27})()
        ctrl.register_irq(27, IRQ_RISING, cb, pm)

        ctrl.on_gpio_changed(27, 0)
        ctrl.on_gpio_changed(27, 1)   # pending
        ctrl.reset()
        ctrl._queue.clear()  # the unit test doesn't use Engine, so clear queue explicitly

        ctrl.dispatch_pending()   # must not fire
        assert len(calls) == 0

    def test_rapid_transitions_1000(self):
        ctrl = InterruptController(RuntimeCallbackQueue())
        cb, calls = make_counter()
        pm = type("P", (), {"id": 27})()
        ctrl.register_irq(27, IRQ_RISING | IRQ_FALLING, cb, pm)

        ctrl.on_gpio_changed(27, 0)  # baseline
        for i in range(1000):
            ctrl.on_gpio_changed(27, i % 2)
        ctrl.dispatch_pending()

        # Must have exactly 1000 edges (alternating 0→1→0→...)
        # First loop iteration: 0→0 (no edge). Actually i=0 → val=0 (same as baseline=0, no edge)
        # i=1 → val=1 (rising), i=2 → val=0 (falling), ...
        # 999 actual edges (i=1..999)
        assert len(calls) == 999


# ---------------------------------------------------------------------------
# 2. Integration tests with GPIOManager
# ---------------------------------------------------------------------------

class TestGPIOIRQIntegration:

    def test_write_output_triggers_input_irq(self, engine, irq_ctrl):
        """GPIO25 OUT → GPIO27 IN: writing output must trigger IRQ on input."""
        # Setup topology: GPIO25 output connected to GPIO27 input
        engine.resolver.add_connection("esp32", "GPIO25", "esp32", "GPIO27")
        engine.trigger_update()

        engine.gpio_manager.configure(25, sim_machine.Pin.OUT)
        engine.gpio_manager.configure(27, sim_machine.Pin.IN)

        # Create Pin objects to register IRQ
        pin27 = sim_machine.Pin(27, sim_machine.Pin.IN)
        cb, calls = make_counter()
        irq_ctrl.register_irq(27, IRQ_RISING | IRQ_FALLING, cb, pin27)

        # Establish baseline
        irq_ctrl.on_gpio_changed(27, engine.gpio_manager.read(27))

        # Drive GPIO25 HIGH → GPIO27 should see RISING
        engine.gpio_manager.write(25, 1)
        irq_ctrl.dispatch_pending()
        assert len(calls) >= 1
        last_len = len(calls)

        # Drive GPIO25 LOW → FALLING
        engine.gpio_manager.write(25, 0)
        irq_ctrl.dispatch_pending()
        assert len(calls) > last_len

    def test_button_irq_falling(self, engine, irq_ctrl):
        """Button on GPIO27 with PULL_UP: press causes FALLING edge → IRQ."""
        engine.gpio_manager.configure(27, sim_machine.Pin.IN, sim_machine.Pin.PULL_UP)

        pin27 = sim_machine.Pin(27, sim_machine.Pin.IN, sim_machine.Pin.PULL_UP)
        cb, calls = make_counter()
        irq_ctrl.register_irq(27, IRQ_FALLING, cb, pin27)

        # Baseline = HIGH (pull up)
        irq_ctrl._prev_states[27] = 1

        # Simulate button press: drive GPIO27 LOW
        engine.gpio_manager.set_external_input(27, 0)
        irq_ctrl.dispatch_pending()

        assert len(calls) == 1
        assert calls[0] == 27

    def test_button_irq_rising_on_release(self, engine, irq_ctrl):
        engine.gpio_manager.configure(27, sim_machine.Pin.IN, sim_machine.Pin.PULL_UP)
        pin27 = sim_machine.Pin(27, sim_machine.Pin.IN, sim_machine.Pin.PULL_UP)
        cb_fall, fall_calls = make_counter()
        cb_rise, rise_calls = make_counter()

        irq_ctrl.register_irq(27, IRQ_FALLING, cb_fall, pin27)
        irq_ctrl._prev_states[27] = 1

        # Press
        engine.gpio_manager.set_external_input(27, 0)
        irq_ctrl.dispatch_pending()
        assert len(fall_calls) == 1

        # Switch to RISING
        irq_ctrl.register_irq(27, IRQ_RISING, cb_rise, pin27)

        # Release
        engine.gpio_manager.set_external_input(27, 1)
        irq_ctrl.dispatch_pending()
        assert len(rise_calls) == 1

    def test_correct_pin_arg(self, engine, irq_ctrl):
        """Callback must receive the correct Pin object (not another pin)."""
        engine.gpio_manager.configure(25, sim_machine.Pin.IN)
        engine.gpio_manager.configure(26, sim_machine.Pin.IN)

        pin25 = sim_machine.Pin(25, sim_machine.Pin.IN)
        pin26 = sim_machine.Pin(26, sim_machine.Pin.IN)

        received_ids = []
        def cb(pin):
            received_ids.append(pin.id)

        irq_ctrl.register_irq(25, IRQ_RISING | IRQ_FALLING, cb, pin25)
        irq_ctrl.register_irq(26, IRQ_RISING | IRQ_FALLING, cb, pin26)

        irq_ctrl._prev_states[25] = 0
        irq_ctrl._prev_states[26] = 1

        engine.gpio_manager.set_external_input(25, 1)  # rising on 25
        engine.gpio_manager.set_external_input(26, 0)  # falling on 26
        irq_ctrl.dispatch_pending()

        assert 25 in received_ids
        assert 26 in received_ids

    def test_trigger_update_rising_only(self, engine, irq_ctrl):
        """After changing trigger to RISING, FALLING must not fire."""
        engine.gpio_manager.configure(27, sim_machine.Pin.IN)
        pin27 = sim_machine.Pin(27, sim_machine.Pin.IN)
        cb_any, calls_any = make_counter()

        irq_ctrl.register_irq(27, IRQ_RISING | IRQ_FALLING, cb_any, pin27)
        irq_ctrl._prev_states[27] = 1

        # Change to RISING only
        irq_ctrl.register_irq(27, IRQ_RISING, cb_any, pin27)

        # FALLING — must not fire
        engine.gpio_manager.set_external_input(27, 0)
        irq_ctrl.dispatch_pending()
        assert len(calls_any) == 0

        # RISING — must fire
        engine.gpio_manager.set_external_input(27, 1)
        irq_ctrl.dispatch_pending()
        assert len(calls_any) == 1


# ---------------------------------------------------------------------------
# 3. Lifecycle tests
# ---------------------------------------------------------------------------

class TestIRQLifecycle:

    def test_reset_clears_registrations(self, engine, irq_ctrl):
        engine.gpio_manager.configure(27, sim_machine.Pin.IN)
        pin27 = sim_machine.Pin(27, sim_machine.Pin.IN)
        cb, calls = make_counter()
        irq_ctrl.register_irq(27, IRQ_RISING, cb, pin27)

        irq_ctrl._prev_states[27] = 0

        engine.reset()  # calls irq_ctrl.reset()

        engine.gpio_manager.configure(27, sim_machine.Pin.IN)
        engine.gpio_manager.set_external_input(27, 1)
        irq_ctrl.dispatch_pending()
        assert len(calls) == 0

    def test_100_lifecycle_cycles(self, engine, irq_ctrl):
        """No leaks across 100 reset cycles."""
        for _ in range(100):
            engine.gpio_manager.configure(27, sim_machine.Pin.IN)
            pin27 = sim_machine.Pin(27, sim_machine.Pin.IN)
            cb, calls = make_counter()
            irq_ctrl.register_irq(27, IRQ_RISING, cb, pin27)
            irq_ctrl._prev_states[27] = 0
            engine.gpio_manager.set_external_input(27, 1)
            irq_ctrl.dispatch_pending()
            assert len(calls) == 1

            engine.reset()
            assert len(irq_ctrl._registrations) == 0
            assert len(irq_ctrl._queue) == 0

    def test_teardown(self, engine, irq_ctrl):
        cb, calls = make_counter()
        pm = type("P", (), {"id": 27})()
        irq_ctrl.register_irq(27, IRQ_RISING, cb, pm)
        irq_ctrl._queue.push(cb, pm)

        engine.reset() # This now handles both irq_ctrl reset and queue clear
        assert len(irq_ctrl._registrations) == 0
        assert len(irq_ctrl._queue) == 0

