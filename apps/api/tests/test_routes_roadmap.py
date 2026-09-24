from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import Clock, FixedClock
from kindred_api.ledger import append_note
from kindred_api.progress import check_in
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import NoteDraft
from kindred_db import EMBEDDING_DIMENSIONS, Plan, TopicNode

AddCourse = Callable[[int], Awaitable[Plan]]
ApiClient = Callable[[Clock, TurnWorker | None], httpx.AsyncClient]
# The evening of day 2 in Kolkata.
DAY_2_EVENING = datetime(2026, 10, 2, 14, 0, tzinfo=UTC)


async def write_note(session: AsyncSession, day: int, at: datetime) -> int:
    node_id = await session.scalar(select(TopicNode.id).where(TopicNode.day == day))
    assert node_id is not None
    return await append_note(
        session,
        node_id=node_id,
        note=NoteDraft(
            body=f"day {day} notes",
            shaky=["?"],
            sources=["https://d.t"],
            share="went ok",
        ),
        written_at=at,
        embedding=[0.5] * EMBEDDING_DIMENSIONS,
        embedding_model="fake-embed",
    )


@pytest.mark.anyio
async def test_the_roadmap_shows_both_learners_on_every_topic(
    api: ApiClient, session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(3)
    await write_note(session, 1, DAY_2_EVENING - timedelta(days=1))
    await write_note(session, 2, DAY_2_EVENING)
    await check_in(session, plan.id, DAY_2_EVENING)

    roadmap = (await api(FixedClock(DAY_2_EVENING), None).get("/roadmap")).json()

    assert (roadmap["plan_title"], roadmap["day"]) == ("T", 2)
    assert (roadmap["streak"], roadmap["gap"]) == (1, 1)
    assert [
        (t["topic"]["day"], t["unlocked"], t["buddy_studied"], t["user_studied"])
        for t in roadmap["topics"]
    ] == [(1, True, True, True), (2, True, True, False), (3, False, False, False)]
    # Locked titles stay readable: it's the user's own plan.
    assert roadmap["topics"][2]["topic"]["title"] == "Topic 3"


@pytest.mark.anyio
async def test_no_roadmap_before_a_plan(api: ApiClient) -> None:
    response = await api(FixedClock(DAY_2_EVENING), None).get("/roadmap")

    assert response.status_code == 404
