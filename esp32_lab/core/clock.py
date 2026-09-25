# -*- coding: utf-8 -*-
import time
from typing import Protocol

class Clock(Protocol):
    def now(self) -> float:
        ...

class SystemClock:
    def now(self) -> float:
        return time.time()

class FakeClock:
    def __init__(self, initial_time: float = 0.0):
        self._now = initial_time

    def now(self) -> float:
        return self._now

    def set_time(self, t: float):
        self._now = t

    def advance(self, seconds: float):
        self._now += seconds
