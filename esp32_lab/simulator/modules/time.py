"""
Module 'time' simulé pour l'environnement MicroPython
Prend en charge sleep, sleep_ms, ticks_ms avec vérification d'interruption
"""

import time as _sys_time
from typing import Callable

_should_stop: Callable[[], bool] | None = None


def set_stop_check_callback(cb: Callable[[], bool]):
    global _should_stop
    _should_stop = cb


def sleep(seconds: float):
    """Pause interruptible en secondes"""
    target = seconds
    chunk = 0.05
    elapsed = 0.0
    while elapsed < target:
        if _should_stop and _should_stop():
            raise InterruptedError("Simulation arrêtée par l'utilisateur.")
        step = min(chunk, target - elapsed)
        _sys_time.sleep(step)
        elapsed += step


def sleep_ms(ms: int):
    sleep(ms / 1000.0)


def sleep_us(us: int):
    sleep(us / 1000000.0)


def ticks_ms() -> int:
    return int(_sys_time.time() * 1000)


def ticks_us() -> int:
    return int(_sys_time.time() * 1000000)


def ticks_diff(t1: int, t2: int) -> int:
    return t1 - t2


def time() -> int:
    """Retourne le nombre de secondes écoulées (Epoch)."""
    return int(_sys_time.time())


def localtime(secs: int | None = None) -> tuple:
    """Retourne un tuple décrivant la date et l'heure courantes."""
    t = _sys_time.localtime(secs) if secs is not None else _sys_time.localtime()
    return (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec, t.tm_wday, t.tm_yday)


def gmtime(secs: int | None = None) -> tuple:
    t = _sys_time.gmtime(secs) if secs is not None else _sys_time.gmtime()
    return (t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec, t.tm_wday, t.tm_yday)


def strftime(format: str, t=None) -> str:
    if t is None:
        return _sys_time.strftime(format)
    return _sys_time.strftime(format, t)


def mktime(t) -> int:
    return int(_sys_time.mktime(t))


def ctime(secs: int | None = None) -> str:
    return _sys_time.ctime(secs) if secs is not None else _sys_time.ctime()
