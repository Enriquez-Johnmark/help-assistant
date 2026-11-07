"""Where all logic reads time, so tests control it (architecture.md)."""

from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    """The one place the system clock is read."""

    def now(self) -> datetime:
        return datetime.now(UTC)  # noqa: TID251


class FixedClock:
    """A clock that only moves when told to."""

    def __init__(self, at: datetime) -> None:
        if at.tzinfo is None:
            raise ValueError("a FixedClock needs a time zone")
        self._at = at

    def now(self) -> datetime:
        return self._at

    def advance(self, by: timedelta) -> None:
        self._at += by
