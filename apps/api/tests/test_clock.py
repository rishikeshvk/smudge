from datetime import UTC, datetime, timedelta, timezone

import pytest

from kindred_api.clock import FixedClock, OffsetClock, SystemClock


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


def test_offset_clock_keeps_ticking_with_its_base() -> None:
    base = FixedClock(datetime(2026, 10, 1, 9, 0, tzinfo=UTC))
    clock = OffsetClock(base, timedelta(days=2))

    base.advance(timedelta(minutes=5))

    assert clock.now() == datetime(2026, 10, 3, 9, 5, tzinfo=UTC)


def test_offset_clock_moves_advances_and_resets() -> None:
    base = FixedClock(datetime(2026, 10, 1, 9, 0, tzinfo=UTC))
    clock = OffsetClock(base, timedelta())

    clock.move_to(datetime(2026, 10, 9, 19, 0, tzinfo=UTC))
    assert clock.now() == datetime(2026, 10, 9, 19, 0, tzinfo=UTC)

    clock.advance(timedelta(hours=1))
    assert clock.now() == datetime(2026, 10, 9, 20, 0, tzinfo=UTC)
    assert clock.offset == timedelta(days=8, hours=11)

    clock.reset()
    assert clock.now() == base.now()


def test_offset_clock_rejects_naive_targets() -> None:
    clock = OffsetClock(SystemClock(), timedelta())

    with pytest.raises(ValueError, match="timezone-aware"):
        clock.move_to(datetime(2026, 10, 1, 9, 0))
