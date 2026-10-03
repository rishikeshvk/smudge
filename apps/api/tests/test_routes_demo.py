from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import Clock, FixedClock
from kindred_api.demo import DemoBudget
from kindred_api.dependencies import get_demo_budget, get_llm
from kindred_api.main import app
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import (
    AuditVerdict,
    Category,
    Classification,
    Draft,
    DraftRequest,
    PersonaContext,
    RetrievedNote,
    Verdict,
)
from kindred_db import Plan, Turn, User
from kindred_gate import TurnComponents
from kindred_llm import LLMUnavailableError

AddCourse = Callable[..., Awaitable[Plan]]
ApiClient = Callable[[Clock, TurnWorker | None, int | None], httpx.AsyncClient]
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)


class Buddy:
    model = "fake"

    def __init__(self, *, down: bool = False) -> None:
        self.down = down
        self.asked_at: list[datetime] = []

    async def classify(self, *args: object) -> Classification:
        if self.down:
            raise LLMUnavailableError("out of credit")
        return Classification(category=Category.OFF_TOPIC, rationale="chat")

    async def retrieve(self, *args: object) -> list[RetrievedNote]:
        return []

    async def noted_slugs(self, now: datetime) -> frozenset[str]:
        self.asked_at.append(now)
        return frozenset()

    async def draft(self, request: DraftRequest, session_id: str) -> Draft:
        return Draft(reply=f"re: {request.message}")

    async def audit(self, *args: object) -> AuditVerdict:
        return AuditVerdict(verdict=Verdict.PASS, rationale="fine")


class FakeRuntime:
    def __init__(self, buddy: Buddy) -> None:
        self.buddy = buddy

    def turn_components(
        self, session: AsyncSession, plan_id: int, persona: PersonaContext
    ) -> TurnComponents:
        b = self.buddy
        return TurnComponents(classifier=b, retriever=b, drafter=b, auditor=b)


@pytest.fixture
def buddy() -> Buddy:
    return Buddy()


@pytest.fixture
def budget() -> DemoBudget:
    return DemoBudget(FixedClock(NOW), daily_turns=3, client_turns_per_hour=2)


@pytest.fixture
def client(api: ApiClient, buddy: Buddy, budget: DemoBudget) -> httpx.AsyncClient:
    connected = api(FixedClock(NOW), None, None)
    app.dependency_overrides[get_demo_budget] = lambda: budget
    app.dependency_overrides[get_llm] = lambda: FakeRuntime(buddy)
    return connected


@pytest.fixture
async def demo_plan(session: AsyncSession, add_course: AddCourse) -> Plan:
    demo = User(timezone="UTC", is_demo=True)
    session.add(demo)
    await session.flush()
    return await add_course(3, demo.id)


@pytest.mark.anyio
async def test_anyone_can_see_the_demo_buddy_and_its_days(
    client: httpx.AsyncClient, demo_plan: Plan
) -> None:
    response = await client.get("/demo")

    assert response.status_code == 200
    body = response.json()
    assert body["buddy_name"] == "Juno"
    assert [d["title"] for d in body["days"]] == ["Topic 1", "Topic 2", "Topic 3"]
    assert body["turns_left"] == 3


@pytest.mark.anyio
async def test_a_visitor_gets_an_audited_reply_on_the_day_they_picked(
    client: httpx.AsyncClient, buddy: Buddy, session: AsyncSession, demo_plan: Plan
) -> None:
    response = await client.post("/demo/turns", json={"message": "hi", "day": 2})

    assert response.status_code == 200
    assert response.json()["reply"] == "re: hi"
    assert response.json()["turns_left"] == 2
    # Day 2 of a plan from 1 Oct, in the evening in Kolkata.
    assert buddy.asked_at == [datetime(2026, 10, 2, 15, 30, tzinfo=UTC)]
    turn = await session.scalar(select(Turn).where(Turn.plan_id == demo_plan.id))
    assert turn is not None and turn.session_id.startswith("demo-")


@pytest.mark.anyio
async def test_a_member_s_plan_is_never_the_demo(
    client: httpx.AsyncClient, add_course: AddCourse
) -> None:
    await add_course(3)

    assert (await client.get("/demo")).status_code == 404
    response = await client.post("/demo/turns", json={"message": "hi", "day": 1})
    assert response.status_code == 404


@pytest.mark.anyio
async def test_days_past_the_plan_are_refused(
    client: httpx.AsyncClient, demo_plan: Plan
) -> None:
    response = await client.post("/demo/turns", json={"message": "hi", "day": 4})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_long_messages_are_refused(
    client: httpx.AsyncClient, demo_plan: Plan
) -> None:
    response = await client.post("/demo/turns", json={"message": "x" * 301, "day": 1})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_one_visitor_runs_out_of_turns_before_everyone_does(
    client: httpx.AsyncClient, demo_plan: Plan
) -> None:
    ask = {"message": "hi", "day": 1}
    me = {"X-Forwarded-For": "1.2.3.4, 100.64.0.1"}

    assert (await client.post("/demo/turns", json=ask, headers=me)).status_code == 200
    assert (await client.post("/demo/turns", json=ask, headers=me)).status_code == 200
    third = await client.post("/demo/turns", json=ask, headers=me)

    assert third.status_code == 429
    assert (await client.post("/demo/turns", json=ask)).status_code == 200
    assert (await client.post("/demo/turns", json=ask)).status_code == 429


@pytest.mark.anyio
async def test_an_unavailable_endpoint_is_a_503(
    client: httpx.AsyncClient, buddy: Buddy, demo_plan: Plan
) -> None:
    buddy.down = True

    response = await client.post("/demo/turns", json={"message": "hi", "day": 1})

    assert response.status_code == 503


@pytest.mark.anyio
async def test_only_the_landing_page_may_call_from_a_browser(
    client: httpx.AsyncClient, demo_plan: Plan
) -> None:
    allowed = await client.get("/demo", headers={"Origin": "https://smudge.expo.app"})
    other = await client.get("/demo", headers={"Origin": "https://evil.example"})

    assert allowed.headers["access-control-allow-origin"] == "https://smudge.expo.app"
    assert "access-control-allow-origin" not in other.headers
