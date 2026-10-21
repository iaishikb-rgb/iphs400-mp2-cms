"""Per-account failed-login limiter (in memory, process-wide)."""
from __future__ import annotations

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60

_failures: dict[str, list[float]] = {}


def _key(email: str) -> str:
    return email.strip().lower()


def _recent(email: str, now: float) -> list[float]:
    key = _key(email)
    recent = [t for t in _failures.get(key, []) if now - t < WINDOW_SECONDS]
    if recent:
        _failures[key] = recent
    else:
        _failures.pop(key, None)
    return recent


def is_locked(email: str, now: float) -> bool:
    return len(_recent(email, now)) >= MAX_FAILURES


def record_failure(email: str, now: float) -> None:
    _recent(email, now)
    _failures.setdefault(_key(email), []).append(now)


def reset() -> None:
    _failures.clear()
