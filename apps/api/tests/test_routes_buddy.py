from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, time

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.clock import Clock, FixedClock
from kindred_api.dependencies import get_ticker
from kindred_api.director import RitualSchedule
from kindred_api.main import app
from kindred_api.study import StudyComponents
from kindred_api.ticker import Ticker
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import (
    AuditVerdict,
    MemoryBrief,
    MemoryUpdate,
    NoteDraft,
    PersonaContext,
    StudyBrief,
)
from kindred_db import Plan
from kindred_gate import TopicMap, TurnComponents

AddCourse = Callable[[int], Awaitable[Plan]]
ApiClient = Callable[[Clock, TurnWorker | None], httpx.AsyncClient]
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)


class NoStudy:
    model = "none"

    async def study(self, brief: StudyBrief, session_id: str) -> NoteDraft:
        raise AssertionError("nothing should be studied")

    async def audit_note(
        self, note: str, topics: TopicMap, now: datetime, session_id: str
    ) -> AuditVerdict:
        raise AssertionError("nothing should be audited")

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise AssertionError("nothing should be embedded")

    async def remember(self, brief: MemoryBrief, session_id: str) -> MemoryUpdate:
        raise AssertionError("nothing should be remembered")


def unused(
    session: AsyncSession, plan_id: int, persona: PersonaContext
) -> TurnComponents:
    raise AssertionError("no turn should run")


@pytest.fixture
def worker(sessions: async_sessionmaker[AsyncSession]) -> TurnWorker:
    return TurnWorker(sessions, FixedClock(NOW), unused)


@pytest.fixture
def ticker(sessions: async_sessionmaker[AsyncSession]) -> Ticker:
    none = NoStudy()
    idle = Ticker(
        sessions,
        FixedClock(NOW),
        lambda: StudyComponents(curator=none, auditor=none, embedder=none),
        lambda: none,
        RitualSchedule(morning=time(8), night=time(21, 30), daily_cap=4),
    )
    app.dependency_overrides[get_ticker] = lambda: idle
    return idle


@pytest.mark.anyio
async def test_buddy_reports_its_name_and_what_it_is_doing(
    api: ApiClient, worker: TurnWorker, ticker: Ticker, add_course: AddCourse
) -> None:
    await add_course(1)
    client = api(FixedClock(NOW), worker)

    assert (await client.get("/buddy")).json() == {
        "name": "Juno",
        "available": True,
        "studying": False,
    }

    worker.available = False
    ticker.studying = True

    status = (await client.get("/buddy")).json()
    assert (status["available"], status["studying"]) == (False, True)


@pytest.mark.anyio
async def test_no_buddy_before_onboarding(
    api: ApiClient, worker: TurnWorker, ticker: Ticker
) -> None:
    response = await api(FixedClock(NOW), worker).get("/buddy")

    assert response.status_code == 404
