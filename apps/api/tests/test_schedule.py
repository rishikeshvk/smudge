from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from kindred_api.schedule import plan_moment

STUDY_TIME = time(19, 0)


def test_day_one_unlocks_at_study_time_in_the_users_zone() -> None:
    kolkata = ZoneInfo("Asia/Kolkata")

    assert plan_moment(date(2026, 10, 1), 1, STUDY_TIME, kolkata) == datetime(
        2026, 10, 1, 13, 30, tzinfo=UTC
    )


def test_later_days_unlock_on_consecutive_dates() -> None:
    kolkata = ZoneInfo("Asia/Kolkata")

    assert plan_moment(date(2026, 10, 1), 14, STUDY_TIME, kolkata) == datetime(
        2026, 10, 14, 13, 30, tzinfo=UTC
    )


def test_unlock_stays_at_local_study_time_across_a_dst_change() -> None:
    new_york = ZoneInfo("America/New_York")
    start = date(2026, 10, 30)

    # DST ends on 2026-11-01, so 19:00 local moves from 23:00Z to 00:00Z.
    assert plan_moment(start, 1, STUDY_TIME, new_york) == datetime(
        2026, 10, 30, 23, 0, tzinfo=UTC
    )
    assert plan_moment(start, 4, STUDY_TIME, new_york) == datetime(
        2026, 11, 3, 0, 0, tzinfo=UTC
    )
