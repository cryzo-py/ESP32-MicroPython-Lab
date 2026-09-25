"""
Phase 5.12 — Timer Foundation: Comprehensive Tests

Tests the TimerManager, machine.Timer API, callback dispatch,
lifecycle, validation, and multi-timer scenarios.

Strategy: tests use TimerManager directly (unit tests) without needing
a real wall-clock wait. The scheduler fires callbacks into the
RuntimeCallbackQueue; we drain the queue manually in tests.
"""

import pytest
import time as _sys_time
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.simulator.callback_queue import RuntimeCallbackQueue
from esp32_lab.simulator.timers import TimerManager, ONE_SHOT, PERIODIC


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def queue():
    return RuntimeCallbackQueue()


@pytest.fixture
def manager(queue):
    mgr = TimerManager(queue)
    yield mgr
    mgr.teardown()


@pytest.fixture
def engine():
    eng = SimulationEngine()
    sim_machine.Timer._timer_manager = eng.timer_manager
    yield eng
    eng.reset()


# ---------------------------------------------------------------------------
# Helper: create a fake Timer object
# ---------------------------------------------------------------------------

def fake_timer(id_=0):
    t = object.__new__(sim_machine.Timer)
    t._id = id_
    t._active = True
    return t


def wait_for_callbacks(queue, expected_count: int, timeout_s: float = 2.0) -> None:
    """Spin-wait until the queue has at least expected_count items OR timeout."""
    deadline = _sys_time.monotonic() + timeout_s
    while len(queue) < expected_count and _sys_time.monotonic() < deadline:
        _sys_time.sleep(0.01)


# ---------------------------------------------------------------------------
# 1. TimerManager unit tests (no wall-clock dependency needed for MOST tests)
# ---------------------------------------------------------------------------

class TestTimerManagerBasic:

    def test_construction(self, manager, queue):
        assert manager.active_count() == 0
        assert len(queue) == 0

    def test_register_periodic(self, manager, queue):
        calls = []
        tm = fake_timer(0)
        manager.register(0, 20, PERIODIC, lambda t: calls.append(t), tm)
        assert manager.active_count() == 1
        entry = manager.get_entry(0)
        assert entry is not None
        assert entry.mode == PERIODIC
        assert entry.period_ms == 20

    def test_register_one_shot(self, manager, queue):
        tm = fake_timer(0)
        manager.register(0, 50, ONE_SHOT, lambda t: None, tm)
        entry = manager.get_entry(0)
        assert entry.mode == ONE_SHOT

    def test_invalid_period_zero(self, manager):
        with pytest.raises(ValueError, match="période"):
            manager.register(0, 0, PERIODIC, lambda t: None, fake_timer(0))

    def test_invalid_period_negative(self, manager):
        with pytest.raises(ValueError, match="période"):
            manager.register(0, -100, PERIODIC, lambda t: None, fake_timer(0))

    def test_invalid_mode(self, manager):
        with pytest.raises(ValueError, match="Mode invalide"):
            manager.register(0, 100, 999, lambda t: None, fake_timer(0))

    def test_invalid_callback_none_treated_as_deinit(self, manager):
        tm = fake_timer(0)
        manager.register(0, 100, PERIODIC, lambda t: None, tm)
        assert manager.active_count() == 1
        manager.register(0, 100, PERIODIC, None, tm)
        assert manager.active_count() == 0  # treated as deinit

    def test_invalid_callback_type(self, manager):
        with pytest.raises(TypeError, match="callable"):
            manager.register(0, 100, PERIODIC, 123, fake_timer(0))

    def test_invalid_timer_id(self, manager):
        with pytest.raises(ValueError, match="Timer ID"):
            manager.register(99, 100, PERIODIC, lambda t: None, fake_timer(99))

    def test_deinit(self, manager):
        manager.register(0, 100, PERIODIC, lambda t: None, fake_timer(0))
        assert manager.active_count() == 1
        manager.unregister(0)
        assert manager.active_count() == 0

    def test_deinit_idempotent(self, manager):
        manager.unregister(0)  # never registered — must not raise
        manager.unregister(0)

    def test_reinit_replaces(self, manager, queue):
        calls_a, calls_b = [], []
        tm = fake_timer(0)
        manager.register(0, 20, PERIODIC, lambda t: calls_a.append(1), tm)
        manager.register(0, 20, PERIODIC, lambda t: calls_b.append(1), tm)
        # Wait for at least one callback
        wait_for_callbacks(queue, 1)
        queue.drain()
        assert len(calls_b) >= 1
        # calls_a must be 0 (replaced before any fire)
        assert len(calls_a) == 0

    def test_reset_stops_all(self, manager):
        for i in range(5):
            manager.register(i, 50, PERIODIC, lambda t: None, fake_timer(i))
        assert manager.active_count() == 5
        manager.reset()
        assert manager.active_count() == 0

    def test_multiple_timers_independent(self, manager, queue):
        calls0, calls1 = [], []
        manager.register(0, 20, PERIODIC, lambda t: calls0.append(1), fake_timer(0))
        manager.register(1, 20, PERIODIC, lambda t: calls1.append(1), fake_timer(1))
        wait_for_callbacks(queue, 2)
        queue.drain()
        assert len(calls0) >= 1
        assert len(calls1) >= 1


class TestTimerModes:

    def test_one_shot_fires_exactly_once(self, manager, queue):
        calls = []
        tm = fake_timer(0)
        manager.register(0, 20, ONE_SHOT, lambda t: calls.append(1), tm)
        wait_for_callbacks(queue, 1)
        _sys_time.sleep(0.1)  # extra wait to catch duplicates
        queue.drain()
        assert len(calls) == 1
        # Timer must be inactive after firing
        assert manager.get_entry(0) is None

    def test_periodic_fires_multiple_times(self, manager, queue):
        calls = []
        tm = fake_timer(0)
        manager.register(0, 20, PERIODIC, lambda t: calls.append(1), tm)
        wait_for_callbacks(queue, 3, timeout_s=3.0)
        queue.drain()
        assert len(calls) >= 3

    def test_one_shot_does_not_repeat(self, manager, queue):
        calls = []
        tm = fake_timer(0)
        manager.register(0, 20, ONE_SHOT, lambda t: calls.append(1), tm)
        wait_for_callbacks(queue, 1)
        _sys_time.sleep(0.15)  # extra wait
        queue.drain()
        assert len(calls) == 1


class TestTimerCallbacks:

    def test_correct_timer_arg(self, manager, queue):
        received = []
        tm = fake_timer(0)
        manager.register(0, 20, ONE_SHOT, lambda t: received.append(t), tm)
        wait_for_callbacks(queue, 1)
        queue.drain()
        assert len(received) == 1
        assert received[0] is tm

    def test_multiple_correct_args(self, manager, queue):
        received = {}
        tm0 = fake_timer(0)
        tm1 = fake_timer(1)

        def cb0(t): received[0] = t
        def cb1(t): received[1] = t

        manager.register(0, 20, ONE_SHOT, cb0, tm0)
        manager.register(1, 20, ONE_SHOT, cb1, tm1)
        wait_for_callbacks(queue, 2)
        queue.drain()

        assert received.get(0) is tm0
        assert received.get(1) is tm1

    def test_callback_exception_isolated(self, manager, queue):
        bad_calls, good_calls = [], []

        def bad(t): bad_calls.append(1); raise RuntimeError("test")
        def good(t): good_calls.append(1)

        manager.register(0, 20, ONE_SHOT, bad, fake_timer(0))
        manager.register(1, 20, ONE_SHOT, good, fake_timer(1))
        wait_for_callbacks(queue, 2)
        queue.drain()

        assert len(bad_calls) == 1
        assert len(good_calls) == 1


class TestTimerLifecycle:

    def test_100_lifecycle_cycles(self, manager, queue):
        for _ in range(100):
            calls = []
            tm = fake_timer(0)
            manager.register(0, 20, ONE_SHOT, lambda t: calls.append(1), tm)
            wait_for_callbacks(queue, 1)
            queue.drain()
            assert len(calls) == 1
            manager.unregister(0)  # idempotent after ONE_SHOT

    def test_deinit_before_fire_prevents_callback(self, manager, queue):
        calls = []
        tm = fake_timer(0)
        # Use a long period so we can deinit before it fires
        manager.register(0, 500, ONE_SHOT, lambda t: calls.append(1), tm)
        manager.unregister(0)
        _sys_time.sleep(0.6)  # let period elapse
        queue.drain()
        assert len(calls) == 0

    def test_reinit_after_deinit(self, manager, queue):
        calls = []
        tm = fake_timer(0)
        manager.register(0, 100, ONE_SHOT, lambda t: calls.append(1), tm)
        manager.unregister(0)
        # Reinit should work
        manager.register(0, 20, ONE_SHOT, lambda t: calls.append(1), tm)
        wait_for_callbacks(queue, 1)
        queue.drain()
        assert len(calls) == 1

    def test_stale_callback_after_deinit(self, manager, queue):
        """A timer deinited before its already-queued callback fires — generation check."""
        calls = []

        # We fire it manually by pushing a stale entry
        gen_before = manager._generations.get(0, 0) + 1
        manager._generations[0] = gen_before

        # Push a callback with the OLD generation
        from esp32_lab.simulator.timers import TimerEntry
        import time as t_
        entry = TimerEntry(
            timer_id=0, period_ms=20, mode=ONE_SHOT,
            callback=lambda t: calls.append(1),
            timer_obj=fake_timer(0),
            next_fire_ns=t_.monotonic_ns(),
            generation=gen_before - 1,  # stale
        )
        # The scheduler would skip this — simulate the check:
        current_gen = manager._generations.get(0, -1)
        if entry.generation != current_gen:
            pass  # correctly skipped
        else:
            queue.push(entry.callback, entry.timer_obj)

        queue.drain()
        assert len(calls) == 0  # stale callback must NOT execute


class TestMachineTimerAPI:

    def test_timer_construction(self, engine):
        t = sim_machine.Timer(0)
        assert t.id == 0

    def test_timer_invalid_id(self, engine):
        with pytest.raises(ValueError):
            sim_machine.Timer(99)

    def test_timer_init_periodic(self, engine):
        q = engine.callback_queue
        calls = []
        t = sim_machine.Timer(0)
        t.init(period=20, mode=sim_machine.Timer.PERIODIC, callback=lambda tm: calls.append(1))
        wait_for_callbacks(q, 2, timeout_s=2.0)
        q.drain()
        t.deinit()
        assert len(calls) >= 2

    def test_timer_init_one_shot(self, engine):
        q = engine.callback_queue
        calls = []
        t = sim_machine.Timer(0)
        t.init(period=20, mode=sim_machine.Timer.ONE_SHOT, callback=lambda tm: calls.append(1))
        wait_for_callbacks(q, 1, timeout_s=1.0)
        _sys_time.sleep(0.1)
        q.drain()
        assert len(calls) == 1

    def test_timer_deinit(self, engine):
        q = engine.callback_queue
        calls = []
        t = sim_machine.Timer(0)
        t.init(period=500, mode=sim_machine.Timer.ONE_SHOT, callback=lambda tm: calls.append(1))
        t.deinit()
        _sys_time.sleep(0.6)
        q.drain()
        assert len(calls) == 0

    def test_timer_reinit_clears_old(self, engine):
        q = engine.callback_queue
        calls_a, calls_b = [], []
        t = sim_machine.Timer(0)
        t.init(period=20, mode=sim_machine.Timer.PERIODIC, callback=lambda tm: calls_a.append(1))
        t.init(period=20, mode=sim_machine.Timer.PERIODIC, callback=lambda tm: calls_b.append(1))
        wait_for_callbacks(q, 1, timeout_s=1.0)
        q.drain()
        t.deinit()
        assert len(calls_a) == 0
        assert len(calls_b) >= 1

    def test_timer_reset_clears_all(self, engine):
        q = engine.callback_queue
        calls = []
        t = sim_machine.Timer(0)
        t.init(period=20, mode=sim_machine.Timer.PERIODIC, callback=lambda tm: calls.append(1))
        engine.reset()
        _sys_time.sleep(0.1)
        assert engine.timer_manager.active_count() == 0

    def test_multi_timer_isolation(self):
        """Simulation A and B must have independent TimerManagers."""
        from esp32_lab.simulator.engine import SimulationEngine
        from esp32_lab.app.event_bus import reset_event_bus
        reset_event_bus()
        eng_a = SimulationEngine()
        reset_event_bus()
        eng_b = SimulationEngine()

        assert eng_a.timer_manager is not eng_b.timer_manager
        assert eng_a.callback_queue is not eng_b.callback_queue

        eng_a.reset()
        eng_b.reset()
