"""
InterruptController — GPIO IRQ dispatch engine for ESP32 MicroPython Lab.

Architecture:
    GPIOManager.write() / set_external_input()
        ↓
    _notify(pin, value)  [existing GPIOManager listener mechanism]
        ↓
    InterruptController.on_gpio_changed(pin, new_value)
        ↓
    Edge detection (RISING / FALLING) vs prev_state
        ↓
    RuntimeCallbackQueue.push(handler, pin_obj)  [thread-safe, shared with Timer]
        ↓
    SimulationWorker.trace_lines() drains the queue
        ↓
    handler(pin_obj)  [executes inside MicroPython sandbox thread]

Design principles:
- NO global state: InterruptController is owned by SimulationEngine
- NO direct callback execution in Qt/GUI thread
- NO shortcut: Button → callback (must go through GPIO electrical state)
- Shared RuntimeCallbackQueue with TimerManager (Phase 5.12 unification)
"""

import threading
from typing import Callable, Optional, Any

from .callback_queue import RuntimeCallbackQueue


# Trigger constants (mirror Pin constants)
IRQ_RISING    = 1
IRQ_FALLING   = 2
IRQ_ANY_EDGE  = 3   # RISING | FALLING


class IRQRegistration:
    """Holds the IRQ configuration for one GPIO pin."""
    __slots__ = ("pin_id", "trigger", "handler", "pin_obj")

    def __init__(self, pin_id: int, trigger: int, handler: Callable, pin_obj: Any):
        self.pin_id  = pin_id
        self.trigger = trigger
        self.handler = handler
        self.pin_obj = pin_obj   # The machine.Pin proxy passed to callback


class InterruptController:
    """
    GPIO edge-detection and IRQ dispatch controller.

    Owned by SimulationEngine.  Never instantiated at module level.
    Uses the shared RuntimeCallbackQueue introduced in Phase 5.12.
    """

    def __init__(self, callback_queue: RuntimeCallbackQueue):
        self._queue = callback_queue
        # pin_id → IRQRegistration  (last registration wins per pin)
        self._registrations: dict[int, IRQRegistration] = {}
        # Previous resolved logical value per pin  (0 or 1)
        self._prev_states: dict[int, int] = {}
        # Lock for registration modifications
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Registration API (called from machine.Pin.irq() inside sandbox)
    # ------------------------------------------------------------------

    def register_irq(self, pin_id: int, trigger: int,
                     handler: Optional[Callable], pin_obj: Any) -> None:
        """
        Register or update an IRQ for the given GPIO pin.
        Passing handler=None disables the IRQ for that pin.
        New registration replaces the old one (MicroPython semantics).
        """
        with self._lock:
            if handler is None:
                self._registrations.pop(pin_id, None)
            else:
                self._registrations[pin_id] = IRQRegistration(
                    pin_id=pin_id,
                    trigger=trigger,
                    handler=handler,
                    pin_obj=pin_obj,
                )

    def unregister_irq(self, pin_id: int) -> None:
        with self._lock:
            self._registrations.pop(pin_id, None)

    # ------------------------------------------------------------------
    # GPIO transition listener (registered with GPIOManager.add_listener)
    # ------------------------------------------------------------------

    def on_gpio_changed(self, pin_id: int, new_value: int) -> None:
        """
        Called by GPIOManager._notify() on every GPIO value change.
        Detects rising/falling edges and queues matching callbacks.
        Thread-safe: may be called from any thread.
        """
        # Normalize value to 0/1
        new_val = 1 if new_value else 0

        old_val = self._prev_states.get(pin_id)
        self._prev_states[pin_id] = new_val

        if old_val is None:
            # First observation: establish baseline, no callback.
            return

        if old_val == new_val:
            # No edge — do not trigger.
            return

        # Determine edge type
        is_rising  = (old_val == 0 and new_val == 1)
        is_falling = (old_val == 1 and new_val == 0)

        with self._lock:
            reg = self._registrations.get(pin_id)

        if reg is None:
            return

        trigger = reg.trigger
        should_fire = (
            (is_rising  and (trigger & IRQ_RISING))  or
            (is_falling and (trigger & IRQ_FALLING))
        )

        if should_fire:
            # Push to shared queue; do NOT call directly here.
            self._queue.push(reg.handler, reg.pin_obj)

    # ------------------------------------------------------------------
    # Legacy compatibility: dispatch_pending delegated to shared queue
    # (called from runtime.py trace_lines for backwards compatibility)
    # ------------------------------------------------------------------

    def dispatch_pending(self) -> None:
        """Drain via shared queue (backward-compat shim for tests)."""
        self._queue.drain()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Clear all IRQ registrations and pending state. Called on engine.reset()."""
        with self._lock:
            self._registrations.clear()
        self._prev_states.clear()

    def teardown(self) -> None:
        """Full cleanup including all references."""
        self.reset()

    def get_registration(self, pin_id: int) -> Optional[IRQRegistration]:
        """Inspection helper for tests."""
        with self._lock:
            return self._registrations.get(pin_id)

    def __repr__(self) -> str:
        return (f"InterruptController(registered={list(self._registrations.keys())})")
