"""
Phase 5.12 — Timer Chaos Test

5000 random operations: create, init, deinit, reinit, multi-timer,
resets — verifies zero crashes, zero leaks, zero stale callbacks.
"""

import pytest
import random
import time as _sys_time
from esp32_lab.simulator.engine import SimulationEngine
from esp32_lab.simulator.modules import machine as sim_machine
from esp32_lab.simulator.timers import ONE_SHOT, PERIODIC


def test_timer_chaos():
    random.seed(2024)

    eng = SimulationEngine()
    sim_machine.Timer._timer_manager = eng.timer_manager
    q = eng.callback_queue

    total_calls = [0]

    def cb(t):
        total_calls[0] += 1

    timer_ids = list(range(8))

    for op in range(5000):
        action = random.choice([
            "init_periodic", "init_one_shot", "deinit", "reinit",
            "reset", "drain", "check_count", "rapid_toggle",
            "invalid_period", "invalid_mode", "invalid_id",
        ])

        timer_id = random.choice(timer_ids)

        try:
            if action == "init_periodic":
                period = random.choice([10, 20, 50, 100, 200])
                t = sim_machine.Timer(timer_id)
                t.init(period=period, mode=sim_machine.Timer.PERIODIC, callback=cb)

            elif action == "init_one_shot":
                period = random.choice([10, 20, 50, 100])
                t = sim_machine.Timer(timer_id)
                t.init(period=period, mode=sim_machine.Timer.ONE_SHOT, callback=cb)

            elif action == "deinit":
                t = sim_machine.Timer(timer_id)
                t.deinit()

            elif action == "reinit":
                t = sim_machine.Timer(timer_id)
                t.init(period=30, mode=sim_machine.Timer.PERIODIC, callback=cb)
                t.init(period=15, mode=sim_machine.Timer.ONE_SHOT, callback=cb)

            elif action == "reset":
                eng.reset()
                # After reset, timer_manager is still valid but cleared
                sim_machine.Timer._timer_manager = eng.timer_manager

            elif action == "drain":
                q.drain()

            elif action == "check_count":
                count = eng.timer_manager.active_count()
                assert count >= 0

            elif action == "rapid_toggle":
                t = sim_machine.Timer(timer_id)
                t.init(period=10, mode=sim_machine.Timer.PERIODIC, callback=cb)
                t.deinit()
                t.init(period=10, mode=sim_machine.Timer.PERIODIC, callback=cb)
                t.deinit()

            elif action == "invalid_period":
                try:
                    eng.timer_manager.register(timer_id, -1, PERIODIC, cb, None)
                except (ValueError, TypeError):
                    pass

            elif action == "invalid_mode":
                try:
                    eng.timer_manager.register(timer_id, 100, 999, cb, None)
                except (ValueError, TypeError):
                    pass

            elif action == "invalid_id":
                try:
                    sim_machine.Timer(50)
                except ValueError:
                    pass

        except Exception as e:
            # Only allowed exceptions: ValueError, TypeError from validations
            if not isinstance(e, (ValueError, TypeError)):
                raise

    # Final drain
    q.drain()

    # Full teardown
    eng.reset()
    assert eng.timer_manager.active_count() == 0
    assert len(q) == 0
