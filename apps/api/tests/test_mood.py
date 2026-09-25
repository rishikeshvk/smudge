from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.mood import STEADY, Tonight, load_mood, mood
from kindred_api.progress import check_in
from kindred_api.study import StudyStatus
from kindred_contracts import Mood, MoodKind, Studying, TopicRef
from kindred_db import Plan

AddCourse = Callable[[int], Awaitable[Plan]]
AddStudy = Callable[..., Awaitable[None]]
KOLKATA = ZoneInfo("Asia/Kolkata")


def at(hour: int) -> datetime:
    return datetime(2026, 10, 2, hour, 0, tzinfo=KOLKATA)


def test_mid_session_the_buddy_is_focused() -> None:
    studying = Studying(topic=TopicRef(slug="iam", title="IAM", day=2), until=at(20))

    assert mood(at(19), studying, None, None) == Mood(
        kind=MoodKind.FOCUSED, reason="mid-way through IAM"
    )


def test_late_at_night_the_buddy_is_tired() -> None:
    fried = Tonight("IAM", StudyStatus.WRITTEN, shaky=3)

    assert mood(at(23), None, fried, None).kind is MoodKind.TIRED
    assert mood(at(2), None, None, None).kind is MoodKind.TIRED
    assert mood(at(6), None, None, None) == STEADY


def test_a_failed_night_leaves_it_flat() -> None:
    assert mood(
        at(20), None, Tonight("IAM", StudyStatus.FAILED, shaky=0), None
    ) == Mood(kind=MoodKind.FLAT, reason="IAM didn't come together tonight")


def test_a_topic_full_of_shaky_points_leaves_it_fried() -> None:
    assert mood(
        at(20), None, Tonight("IAM", StudyStatus.WRITTEN, shaky=3), None
    ) == Mood(kind=MoodKind.FRIED, reason="IAM was a lot")
    assert (
        mood(at(20), None, Tonight("IAM", StudyStatus.WRITTEN, shaky=1), None) == STEADY
    )


def test_a_point_the_user_helped_sort_out_lifts_the_mood() -> None:
    iam = TopicRef(slug="iam", title="IAM", day=2)
    fried = Tonight("S3", StudyStatus.WRITTEN, shaky=3)

    assert mood(at(20), None, fried, iam) == Mood(
        kind=MoodKind.UPBEAT, reason="IAM finally clicked, thanks to you"
    )


@pytest.mark.anyio
async def test_mood_comes_from_todays_study(
    session: AsyncSession, add_course: AddCourse, add_study: AddStudy
) -> None:
    plan = await add_course(2)
    evening = datetime(2026, 10, 2, 14, 0, tzinfo=UTC)
    await add_study(1, evening - timedelta(days=1), failed=True)
    await add_study(2, evening, shaky=["a", "b", "c"])

    assert (await load_mood(session, plan.id, KOLKATA, None, evening)).kind is (
        MoodKind.FRIED
    )
    before = evening - timedelta(minutes=1)
    assert await load_mood(session, plan.id, KOLKATA, None, before) == STEADY


@pytest.mark.anyio
async def test_the_users_own_progress_never_sets_the_mood(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(3)
    evening = datetime(2026, 10, 3, 14, 0, tzinfo=UTC)
    # Three days in and the user has done nothing: still no reason to feel down.
    assert await load_mood(session, plan.id, KOLKATA, None, evening) == STEADY
    await check_in(session, plan.id, evening)
    assert await load_mood(session, plan.id, KOLKATA, None, evening) == STEADY
