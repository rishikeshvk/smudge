from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.study_window import load_studying
from kindred_db import Plan

AddCourse = Callable[[int], Awaitable[Plan]]
# 19:00 on day 2 in Kolkata, when topic 2 unlocks.
DAY_2_STUDY = datetime(2026, 10, 2, 13, 30, tzinfo=UTC)
HOUR = timedelta(hours=1)


@pytest.mark.anyio
async def test_the_buddy_studies_from_the_study_time_for_the_session(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(3)

    async def studying(now: datetime) -> tuple[int, datetime] | None:
        found = await load_studying(session, plan.id, HOUR, now)
        return None if found is None else (found.topic.day, found.until)

    assert await studying(DAY_2_STUDY - timedelta(minutes=1)) is None
    assert await studying(DAY_2_STUDY) == (2, DAY_2_STUDY + HOUR)
    assert await studying(DAY_2_STUDY + timedelta(minutes=59)) == (
        2,
        DAY_2_STUDY + HOUR,
    )
    assert await studying(DAY_2_STUDY + HOUR) is None
