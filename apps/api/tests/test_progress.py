from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.progress import check_in, studied_slugs
from kindred_contracts import TopicRef
from kindred_db import Plan

AddCourse = Callable[[int], Awaitable[Plan]]
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)


@pytest.mark.anyio
async def test_check_ins_mark_topics_in_plan_order(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(2)

    first = await check_in(session, plan.id, NOW)
    second = await check_in(session, plan.id, NOW)

    assert first == TopicRef(slug="topic-1", title="Topic 1", day=1)
    assert second == TopicRef(slug="topic-2", title="Topic 2", day=2)
    assert await check_in(session, plan.id, NOW) is None


@pytest.mark.anyio
async def test_studied_topics_are_those_checked_in_by_now(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(3)
    await check_in(session, plan.id, NOW)
    await check_in(session, plan.id, NOW + timedelta(days=1))

    assert await studied_slugs(session, plan.id, NOW) == {"topic-1"}
    assert await studied_slugs(session, plan.id, NOW + timedelta(days=1)) == {
        "topic-1",
        "topic-2",
    }
