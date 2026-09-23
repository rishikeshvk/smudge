from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.clock import Clock, FixedClock
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
from kindred_db import Plan
from kindred_gate import TurnComponents

AddCourse = Callable[[int], Awaitable[Plan]]
ApiClient = Callable[[Clock, TurnWorker | None], httpx.AsyncClient]
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)


class Echo:
    model = "echo"

    async def classify(self, *args: object) -> Classification:
        return Classification(category=Category.OFF_TOPIC, rationale="chat")

    async def retrieve(self, *args: object) -> list[RetrievedNote]:
        return []

    async def draft(self, request: DraftRequest, session_id: str) -> Draft:
        return Draft(reply=f"re: {request.message}")

    async def audit(self, *args: object) -> AuditVerdict:
        return AuditVerdict(verdict=Verdict.PASS, rationale="fine")


def echo(
    session: AsyncSession, plan_id: int, persona: PersonaContext
) -> TurnComponents:
    fake = Echo()
    return TurnComponents(classifier=fake, retriever=fake, drafter=fake, auditor=fake)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture
def worker(sessions: async_sessionmaker[AsyncSession], clock: FixedClock) -> TurnWorker:
    return TurnWorker(sessions, clock, echo)


@pytest.fixture
def client(api: ApiClient, clock: FixedClock, worker: TurnWorker) -> httpx.AsyncClient:
    return api(clock, worker)


@pytest.mark.anyio
async def test_a_message_is_queued_then_answered(
    client: httpx.AsyncClient, worker: TurnWorker, add_course: AddCourse
) -> None:
    await add_course(3)

    sent = await client.post("/chat/messages", json={"text": "hi"})

    assert sent.status_code == 202
    assert sent.json()["stage"] == "queued"
    assert sent.json()["speaker"] == "user"

    await worker.drain()
    status = await client.get(f"/chat/messages/{sent.json()['id']}")

    assert status.json()["message"]["stage"] == "answered"
    reply = status.json()["reply"]
    assert reply["speaker"] == "buddy"
    assert reply["text"] == "re: hi"
    assert reply["stage"] is None
    assert reply["turn_id"] is not None


@pytest.mark.anyio
async def test_the_thread_lists_both_sides_oldest_first(
    client: httpx.AsyncClient, worker: TurnWorker, add_course: AddCourse
) -> None:
    await add_course(3)
    await client.post("/chat/messages", json={"text": "hi"})
    await worker.drain()

    thread = await client.get("/chat/messages")

    assert [(m["speaker"], m["text"]) for m in thread.json()] == [
        ("user", "hi"),
        ("buddy", "re: hi"),
    ]


@pytest.mark.anyio
async def test_the_thread_hides_messages_after_a_clock_rewind(
    client: httpx.AsyncClient, clock: FixedClock, add_course: AddCourse
) -> None:
    await add_course(3)
    await client.post("/chat/messages", json={"text": "hi"})

    clock.set(NOW - timedelta(days=1))

    assert (await client.get("/chat/messages")).json() == []


@pytest.mark.anyio
async def test_chat_needs_a_plan(client: httpx.AsyncClient) -> None:
    response = await client.post("/chat/messages", json={"text": "hi"})

    assert response.status_code == 409


@pytest.mark.anyio
async def test_empty_messages_are_rejected(
    client: httpx.AsyncClient, add_course: AddCourse
) -> None:
    await add_course(3)

    assert (await client.post("/chat/messages", json={"text": ""})).status_code == 422


@pytest.mark.anyio
async def test_unknown_messages_are_not_found(client: httpx.AsyncClient) -> None:
    assert (await client.get("/chat/messages/999999")).status_code == 404
