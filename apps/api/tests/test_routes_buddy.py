from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.clock import Clock, FixedClock
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import PersonaContext
from kindred_db import Plan
from kindred_gate import TurnComponents

AddCourse = Callable[[int], Awaitable[Plan]]
ApiClient = Callable[[Clock, TurnWorker | None], httpx.AsyncClient]
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)


def unused(
    session: AsyncSession, plan_id: int, persona: PersonaContext
) -> TurnComponents:
    raise AssertionError("no turn should run")


@pytest.fixture
def worker(sessions: async_sessionmaker[AsyncSession]) -> TurnWorker:
    return TurnWorker(sessions, FixedClock(NOW), unused)


@pytest.mark.anyio
async def test_buddy_reports_its_name_and_availability(
    api: ApiClient, worker: TurnWorker, add_course: AddCourse
) -> None:
    await add_course(1)
    client = api(FixedClock(NOW), worker)

    assert (await client.get("/buddy")).json() == {"name": "Juno", "available": True}

    worker.available = False

    assert (await client.get("/buddy")).json()["available"] is False


@pytest.mark.anyio
async def test_no_buddy_before_onboarding(api: ApiClient, worker: TurnWorker) -> None:
    response = await api(FixedClock(NOW), worker).get("/buddy")

    assert response.status_code == 404
