from __future__ import annotations

from datetime import datetime, timedelta, timezone
import time


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def monotonic(self) -> float:
        return time.monotonic()


class DemoClock:
    """Deterministic clock used only for the committed synthetic demonstration."""

    def __init__(self, start: datetime | None = None, tick_seconds: float = 1.0):
        self._start = start or datetime(2026, 6, 1, 22, 0, tzinfo=timezone.utc)
        self._elapsed = 0.0
        self._tick = tick_seconds

    def now(self) -> datetime:
        value = self._start + timedelta(seconds=self._elapsed)
        self._elapsed += self._tick
        return value

    def monotonic(self) -> float:
        return self._elapsed


def isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
