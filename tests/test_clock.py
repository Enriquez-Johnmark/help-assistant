from datetime import UTC, datetime, timedelta

import pytest

from help_assistant.clock import FixedClock, SystemClock


def test_a_fixed_clock_moves_only_when_told() -> None:
    clock = FixedClock(datetime(2026, 11, 7, 8, 0, tzinfo=UTC))
    assert clock.now() == datetime(2026, 11, 7, 8, 0, tzinfo=UTC)
    clock.advance(timedelta(days=1))
    assert clock.now() == datetime(2026, 11, 8, 8, 0, tzinfo=UTC)


def test_a_fixed_clock_needs_a_time_zone() -> None:
    with pytest.raises(ValueError, match="time zone"):
        FixedClock(datetime(2026, 11, 7))  # noqa: DTZ001


def test_the_system_clock_is_in_utc() -> None:
    assert SystemClock().now().tzinfo is UTC
