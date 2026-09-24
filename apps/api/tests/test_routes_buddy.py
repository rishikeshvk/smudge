from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, time, timedelta

import httpx
import httpx2
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.clock import Clock, FixedClock
from kindred_api.dependencies import get_ticker
from kindred_api.director import RitualSchedule
from kindred_api.main import app
from kindred_api.push import Pusher
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

NO_NETWORK = httpx2.MockTransport(lambda request: httpx2.Response(500))
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
        Pusher(httpx2.AsyncClient(transport=NO_NETWORK), "https://push.test"),
    )
    app.dependency_overrides[get_ticker] = lambda: idle
    return idle


@pytest.mark.anyio
async def test_buddy_reports_its_name_and_what_it_is_doing(
    api: ApiClient, worker: TurnWorker, add_course: AddCourse
) -> None:
    await add_course(1)
    client = api(FixedClock(NOW), worker)

    assert (await client.get("/buddy")).json() == {
        "name": "Juno",
        "mood": {"kind": "steady", "reason": None},
        "available": True,
        "studying": None,
    }

    worker.available = False

    assert (await client.get("/buddy")).json()["available"] is False


@pytest.mark.anyio
async def test_the_buddy_is_studying_during_its_session(
    api: ApiClient, worker: TurnWorker, add_course: AddCourse
) -> None:
    await add_course(1)
    # 19:30 in Kolkata on day 1: half an hour into the hour from 19:00.
    during = datetime(2026, 10, 1, 14, 0, tzinfo=UTC)

    status = (await api(FixedClock(during), worker).get("/buddy")).json()

    assert status["studying"] == {
        "topic": {"slug": "topic-1", "title": "Topic 1", "day": 1},
        "until": "2026-10-01T14:30:00Z",
    }
    assert status["mood"] == {"kind": "focused", "reason": "mid-way through Topic 1"}


@pytest.mark.anyio
async def test_no_buddy_before_onboarding(
    api: ApiClient, worker: TurnWorker, ticker: Ticker
) -> None:
    response = await api(FixedClock(NOW), worker).get("/buddy")

    assert response.status_code == 404


@pytest.mark.anyio
async def test_the_user_can_study_along_only_during_a_session(
    api: ApiClient, worker: TurnWorker, add_course: AddCourse
) -> None:
    await add_course(1)
    during = datetime(2026, 10, 1, 14, 0, tzinfo=UTC)

    refused = await api(FixedClock(during - timedelta(hours=1)), worker).post(
        "/buddy/study-together"
    )
    joined = await api(FixedClock(during), worker).post("/buddy/study-together")

    assert refused.status_code == 409
    message = joined.json()
    assert (message["speaker"], message["stage"], message["reaction"]) == (
        "user",
        "answered",
        "📚",
    )
    assert message["card"] == {
        "kind": "study_together",
        "topic": {"slug": "topic-1", "title": "Topic 1", "day": 1},
        "until": "2026-10-01T14:30:00Z",
    }
