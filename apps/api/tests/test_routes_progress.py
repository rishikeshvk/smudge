from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.clock import Clock, FixedClock
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import PersonaContext
from kindred_db import Plan, StudyCheckin
from kindred_gate import TurnComponents

AddCourse = Callable[[int], Awaitable[Plan]]
ApiClient = Callable[[Clock, TurnWorker | None], httpx.AsyncClient]
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)


OKAY = {"feeling": "okay"}


def unused(
    session: AsyncSession, plan_id: int, persona: PersonaContext
) -> TurnComponents:
    raise AssertionError("no turn should run")


@pytest.fixture
def worker(sessions: async_sessionmaker[AsyncSession]) -> TurnWorker:
    """Only woken: nothing drains the queue in these tests."""
    return TurnWorker(sessions, FixedClock(NOW), unused)


@pytest.mark.anyio
async def test_each_check_in_marks_the_next_topic(
    api: ApiClient, worker: TurnWorker, add_course: AddCourse
) -> None:
    await add_course(2)
    client = api(FixedClock(NOW), worker)

    first = await client.post("/progress/checkins", json=OKAY)
    second = await client.post("/progress/checkins", json=OKAY)
    third = await client.post("/progress/checkins", json=OKAY)

    assert first.json() == {"slug": "topic-1", "title": "Topic 1", "day": 1}
    assert second.json()["slug"] == "topic-2"
    assert third.status_code == 409


@pytest.mark.anyio
async def test_check_ins_need_a_plan(api: ApiClient, worker: TurnWorker) -> None:
    response = await api(FixedClock(NOW), worker).post("/progress/checkins", json=OKAY)

    assert response.status_code == 409


@pytest.mark.anyio
async def test_a_check_in_tells_the_buddy_how_it_went(
    api: ApiClient, worker: TurnWorker, session: AsyncSession, add_course: AddCourse
) -> None:
    await add_course(1)
    client = api(FixedClock(NOW), worker)

    await client.post(
        "/progress/checkins", json={"feeling": "rough", "fuzzy": "why regions?"}
    )

    [message] = (await client.get("/chat/messages")).json()
    assert (
        message["text"] == "finished Topic 1, felt rough. still fuzzy on: why regions?"
    )
    assert message["stage"] == "queued"
    assert message["card"] == {
        "kind": "checkin",
        "topic": {"slug": "topic-1", "title": "Topic 1", "day": 1},
        "feeling": "rough",
        "fuzzy": "why regions?",
    }
    checkin = await session.scalar(select(StudyCheckin))
    assert checkin is not None
    assert (checkin.feeling, checkin.fuzzy) == ("rough", "why regions?")
