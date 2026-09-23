from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """A clock that only moves when told to, for tests, probes and dev time travel."""

    def __init__(self, at: datetime) -> None:
        self._at = _require_aware(at)

    def now(self) -> datetime:
        return self._at

    def set(self, at: datetime) -> None:
        self._at = _require_aware(at)

    def advance(self, delta: timedelta) -> None:
        self._at += delta


class OffsetClock:
    """Real time shifted by an offset, so dev time travel keeps ticking."""

    def __init__(self, base: Clock, offset: timedelta) -> None:
        self._base = base
        self.offset = offset

    def now(self) -> datetime:
        return self._base.now() + self.offset

    def move_to(self, at: datetime) -> None:
        self.offset = _require_aware(at) - self._base.now()

    def advance(self, delta: timedelta) -> None:
        self.offset += delta

    def reset(self) -> None:
        self.offset = timedelta()


def _require_aware(at: datetime) -> datetime:
    if at.tzinfo is None:
        raise ValueError("clock times must be timezone-aware")
    return at.astimezone(UTC)
