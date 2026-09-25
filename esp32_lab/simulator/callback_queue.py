"""
RuntimeCallbackQueue — Shared thread-safe callback queue for ESP32 MicroPython Lab.

Both InterruptController (Phase 5.11) and TimerManager (Phase 5.12) push callbacks
into this single queue.  SimulationWorker drains it between Python lines via sys.settrace.

This unifies the callback execution architecture so there is exactly ONE path
through which user Python callbacks are dispatched inside the sandbox.

Thread-safety: collections.deque.append / popleft are GIL-atomic on CPython.
"""

import collections
import sys
from typing import Any, Callable, Optional


class RuntimeCallbackQueue:
    """
    Single producer-consumer callback queue.

    Producers (any thread):
        queue.push(handler, arg)

    Consumer (MicroPython worker thread via sys.settrace):
        queue.drain()
    """

    def __init__(self):
        self._pending: collections.deque = collections.deque()
        # Re-entrancy guard: prevents recursive drain inside callbacks
        self._draining: bool = False

    def push(self, handler: Callable, arg: Any) -> None:
        """Enqueue a (handler, arg) pair for execution in the sandbox thread."""
        self._pending.append((handler, arg))

    def drain(self) -> None:
        """
        Drain all pending callbacks.
        Must only be called from within the MicroPython sandbox thread.
        Re-entrant calls (e.g. callback queuing another callback) are deferred
        to the next drain() invocation via the _draining guard.
        """
        if self._draining:
            return
        self._draining = True
        try:
            while self._pending:
                try:
                    handler, arg = self._pending.popleft()
                except IndexError:
                    break
                try:
                    handler(arg)
                except Exception as exc:
                    # Isolate callback errors — report but continue.
                    print(f"[Callback error]: {type(exc).__name__}: {exc}",
                          file=sys.stdout)
        finally:
            self._draining = False

    def clear(self) -> None:
        self._pending.clear()
        self._draining = False

    def __len__(self) -> int:
        return len(self._pending)
