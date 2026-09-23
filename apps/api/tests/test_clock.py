from datetime import UTC, datetime, timedelta, timezone

import pytest

from kindred_api.clock import FixedClock, SystemClock


def test_system_clock_returns_aware_utc() -> None:
    assert SystemClock().now().tzinfo is UTC


def test_fixed_clock_stays_put_until_moved() -> None:
    at = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
    clock = FixedClock(at)

    assert clock.now() == at
    assert clock.now() == at


def test_fixed_clock_advances_and_sets() -> None:
    clock = FixedClock(datetime(2026, 10, 1, 9, 0, tzinfo=UTC))

    clock.advance(timedelta(days=1))
    assert clock.now() == datetime(2026, 10, 2, 9, 0, tzinfo=UTC)

    clock.set(datetime(2026, 10, 5, 19, 0, tzinfo=UTC))
    assert clock.now() == datetime(2026, 10, 5, 19, 0, tzinfo=UTC)


def test_fixed_clock_normalises_to_utc() -> None:
    ist = timezone(timedelta(hours=5, minutes=30))

    clock = FixedClock(datetime(2026, 10, 1, 19, 0, tzinfo=ist))

    assert clock.now() == datetime(2026, 10, 1, 13, 30, tzinfo=UTC)
    assert clock.now().tzinfo is UTC


def test_fixed_clock_rejects_naive_times() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        FixedClock(datetime(2026, 10, 1, 9, 0))
