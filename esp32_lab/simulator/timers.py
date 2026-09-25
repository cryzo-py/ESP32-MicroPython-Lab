"""
TimerManager — Hardware-timer emulation for ESP32 MicroPython Lab.

Architecture:
    machine.Timer.init(period, mode, callback)
        ↓
    TimerManager.register(timer_id, period_ms, mode, callback, timer_obj)
        ↓
    Background scheduler thread (one per SimulationEngine)
        ↓
    RuntimeCallbackQueue.push(callback, timer_obj)   [thread-safe]
        ↓
    SimulationWorker.trace_lines() drains queue
        ↓
    callback(timer_obj)   [executes inside MicroPython sandbox]

Design principles:
- Owned by SimulationEngine — NO global state
- Single background scheduler thread (not one thread per timer)
- Callbacks queued into RuntimeCallbackQueue (shared with IRQ system)
- Generation counter prevents stale callbacks after deinit/reinit
- Deterministic ordering: timer ID ascending for equal due-times
- No blocking sleep per timer
- No Timer → Device shortcuts

Timing: wall-clock monotonic (time.monotonic_ns).
The simulator does not claim cycle-accurate ESP32 hardware timing.
Educational-quality deterministic scheduling is the goal.
"""

import threading
import time as _sys_time
from typing import Any, Callable, Optional

from .callback_queue import RuntimeCallbackQueue


# Timer mode constants (mirror machine.Timer constants)
ONE_SHOT = 0
PERIODIC = 1

# Supported hardware timer IDs on ESP32 (0-3 hardware timers + logical extras)
# We expose 0..15 as logical educational timers.
MIN_TIMER_ID = 0
MAX_TIMER_ID = 15

# Minimum allowed period in ms
MIN_PERIOD_MS = 1


class TimerEntry:
    """Internal state for one active timer."""
    __slots__ = (
        "timer_id", "period_ms", "mode", "callback", "timer_obj",
        "next_fire_ns", "generation", "active",
    )

    def __init__(self, timer_id: int, period_ms: int, mode: int,
                 callback: Callable, timer_obj: Any,
                 next_fire_ns: int, generation: int):
        self.timer_id    = timer_id
        self.period_ms   = period_ms
        self.mode        = mode
        self.callback    = callback
        self.timer_obj   = timer_obj
        self.next_fire_ns = next_fire_ns
        self.generation  = generation
        self.active      = True


class TimerManager:
    """
    Manages all simulation timers for one SimulationEngine instance.

    Never instantiated at module level.
    Thread-safe for: register / unregister / reset / teardown.
    """

    # Scheduler sleep granularity (ms).  Lower = more responsive, more CPU.
    _SCHEDULER_GRANULARITY_MS = 10

    def __init__(self, callback_queue: RuntimeCallbackQueue):
        self._queue = callback_queue
        self._lock  = threading.Lock()
        # timer_id → TimerEntry
        self._timers: dict[int, TimerEntry] = {}
        # Per-timer-id generation counter (incremented on each register/deinit)
        self._generations: dict[int, int] = {}
        # Scheduler thread
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # Public API (called from machine.Timer inside MicroPython sandbox)
    # ------------------------------------------------------------------

    def register(self, timer_id: int, period_ms: int, mode: int,
                 callback: Callable, timer_obj: Any) -> None:
        """
        Register (or re-register) a timer.
        Replaces any existing timer with the same ID.
        """
        # Validation
        if not (MIN_TIMER_ID <= timer_id <= MAX_TIMER_ID):
            raise ValueError(
                f"Timer ID {timer_id} invalide. "
                f"Valeurs acceptées: {MIN_TIMER_ID}..{MAX_TIMER_ID}"
            )
        if not isinstance(period_ms, int) or period_ms < MIN_PERIOD_MS:
            raise ValueError(
                f"Période invalide: {period_ms!r}. "
                f"La période doit être un entier ≥ {MIN_PERIOD_MS} ms."
            )
        if mode not in (ONE_SHOT, PERIODIC):
            raise ValueError(
                f"Mode invalide: {mode!r}. "
                f"Valeurs acceptées: Timer.ONE_SHOT ({ONE_SHOT}), "
                f"Timer.PERIODIC ({PERIODIC})"
            )
        if callback is None:
            # MicroPython accepts None to disable; treat as deinit
            self.unregister(timer_id)
            return
        if not callable(callback):
            raise TypeError(
                f"callback doit être callable, reçu: {type(callback).__name__!r}"
            )

        now_ns = _sys_time.monotonic_ns()
        period_ns = period_ms * 1_000_000
        next_fire_ns = now_ns + period_ns

        with self._lock:
            # Bump generation to invalidate any queued callbacks from old config
            gen = self._generations.get(timer_id, 0) + 1
            self._generations[timer_id] = gen

            entry = TimerEntry(
                timer_id=timer_id,
                period_ms=period_ms,
                mode=mode,
                callback=callback,
                timer_obj=timer_obj,
                next_fire_ns=next_fire_ns,
                generation=gen,
            )
            self._timers[timer_id] = entry

        self._ensure_scheduler_running()

    def unregister(self, timer_id: int) -> None:
        """Deactivate a timer (deinit). Idempotent."""
        with self._lock:
            entry = self._timers.pop(timer_id, None)
            if entry is not None:
                entry.active = False
            # Bump generation so any already-queued callbacks are ignored
            self._generations[timer_id] = self._generations.get(timer_id, 0) + 1

    # ------------------------------------------------------------------
    # Scheduler
    # ------------------------------------------------------------------

    def _ensure_scheduler_running(self) -> None:
        with self._lock:
            if self._running and self._thread and self._thread.is_alive():
                return
            self._running = True
            self._stop_event.clear()
            self._thread = threading.Thread(
                target=self._scheduler_loop,
                name="TimerManager-Scheduler",
                daemon=True,
            )
            self._thread.start()

    def _scheduler_loop(self) -> None:
        """Background thread: checks for due timers and enqueues callbacks."""
        granularity_s = self._SCHEDULER_GRANULARITY_MS / 1000.0
        while not self._stop_event.wait(timeout=granularity_s):
            if not self._running:
                break
            self._tick()

    def _tick(self) -> None:
        """Fire all due timers at this moment."""
        now_ns = _sys_time.monotonic_ns()
        due: list[TimerEntry] = []

        with self._lock:
            for entry in sorted(self._timers.values(), key=lambda e: e.timer_id):
                if entry.active and entry.next_fire_ns <= now_ns:
                    due.append(entry)
                    if entry.mode == PERIODIC:
                        # Advance by period (prevents drift accumulation)
                        entry.next_fire_ns += entry.period_ms * 1_000_000
                        # If still behind (heavy load), skip to next valid future
                        while entry.next_fire_ns <= now_ns:
                            entry.next_fire_ns += entry.period_ms * 1_000_000
                    else:
                        # ONE_SHOT: deactivate
                        entry.active = False
                        self._timers.pop(entry.timer_id, None)

        # Enqueue callbacks outside the lock (push is GIL-atomic)
        expected_gen = {}
        with self._lock:
            expected_gen = dict(self._generations)

        for entry in due:
            # Generation check: if timer was deinited/reinited since we captured it,
            # skip the stale callback.
            with self._lock:
                current_gen = self._generations.get(entry.timer_id, -1)
            if entry.generation != current_gen:
                continue  # stale
            self._queue.push(entry.callback, entry.timer_obj)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Stop all timers and clear state. Called on engine.reset()."""
        self._stop_scheduler()
        with self._lock:
            self._timers.clear()
            self._generations.clear()

    def teardown(self) -> None:
        """Full cleanup. Called on engine teardown."""
        self.reset()

    def _stop_scheduler(self) -> None:
        self._running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self._thread = None

    # ------------------------------------------------------------------
    # Inspection (for tests)
    # ------------------------------------------------------------------

    def get_entry(self, timer_id: int) -> Optional[TimerEntry]:
        with self._lock:
            return self._timers.get(timer_id)

    def active_count(self) -> int:
        with self._lock:
            return len(self._timers)

    def __repr__(self) -> str:
        with self._lock:
            return f"TimerManager(active={list(self._timers.keys())})"
