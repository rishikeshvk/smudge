from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, time, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.plans import CurrentPlan, load_current_plan
from kindred_api.replan import (
    ReplanError,
    change_study_time,
    load_movable,
    pause,
    pull_earlier,
)
from kindred_db import Plan, StudySession, TopicNode, TopicPrerequisite

AddCourse = Callable[[int], Awaitable[Plan]]
# 12:00 on day 2 in Kolkata: day 1 is unlocked and studied, day 2 unlocks tonight.
NOW = datetime(2026, 10, 2, 6, 30, tzinfo=UTC)


async def course(
    session: AsyncSession, add_course: AddCourse, days: int
) -> CurrentPlan:
    await add_course(days)
    day_1 = await node(session, "topic-1")
    session.add(StudySession(node_id=day_1.id, status="written", at=NOW, attempts=[]))
    await session.flush()
    plan = await load_current_plan(session)
    assert plan is not None
    return plan


async def node(session: AsyncSession, slug: str) -> TopicNode:
    found = await session.scalar(select(TopicNode).where(TopicNode.slug == slug))
    assert found is not None
    return found


async def schedule(session: AsyncSession) -> list[tuple[int, str, datetime]]:
    await session.commit()
    rows = await session.scalars(select(TopicNode).order_by(TopicNode.day))
    return [(n.day, n.slug, n.unlock_at) for n in rows]


def unlock(day: int, at: time = time(19)) -> datetime:
    local = datetime(2026, 10, day, at.hour, at.minute, tzinfo=UTC)
    return local - timedelta(hours=5, minutes=30)


@pytest.mark.anyio
async def test_a_pulled_topic_takes_tonights_slot_and_the_rest_move_back(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await course(session, add_course, 5)

    await pull_earlier(session, plan, "topic-4", NOW)

    assert await schedule(session) == [
        (1, "topic-1", unlock(1)),
        (2, "topic-4", unlock(2)),
        (3, "topic-2", unlock(3)),
        (4, "topic-3", unlock(4)),
        (5, "topic-5", unlock(5)),
    ]


@pytest.mark.anyio
async def test_a_topic_needs_its_prerequisites_before_the_slot(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await course(session, add_course, 4)
    session.add(
        TopicPrerequisite(
            node_id=(await node(session, "topic-4")).id,
            prerequisite_id=(await node(session, "topic-3")).id,
        )
    )
    await session.flush()

    pullable = (await load_movable(session, plan.id, NOW)).pullable()

    assert [n.slug for n in pullable] == ["topic-3"]
    with pytest.raises(ReplanError):
        await pull_earlier(session, plan, "topic-4", NOW)


@pytest.mark.anyio
async def test_unlocked_or_studied_topics_never_move(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await course(session, add_course, 3)

    for slug in ("topic-1", "topic-2"):
        with pytest.raises(ReplanError):
            await pull_earlier(session, plan, slug, NOW)
    await pause(session, plan, 2, NOW)

    assert await schedule(session) == [
        (1, "topic-1", unlock(1)),
        (4, "topic-2", unlock(4)),
        (5, "topic-3", unlock(5)),
    ]


@pytest.mark.anyio
async def test_a_new_study_time_moves_only_the_topics_ahead(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await course(session, add_course, 2)

    await change_study_time(session, plan, time(7, 30), NOW)

    assert await schedule(session) == [
        (1, "topic-1", unlock(1)),
        (2, "topic-2", unlock(2, time(7, 30))),
    ]
    assert (await session.get_one(Plan, plan.id)).study_time == time(7, 30)
