from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.chat import post_message
from kindred_api.clock import FixedClock
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import (
    AuditVerdict,
    Category,
    ChatTurn,
    Classification,
    Draft,
    DraftRequest,
    PersonaContext,
    RetrievedNote,
    Speaker,
    TurnStage,
    Verdict,
)
from kindred_db import Message, Plan, Turn
from kindred_gate import TopicMap, TurnComponents
from kindred_llm import LLMUnavailableError

AddCourse = Callable[[int], Awaitable[Plan]]
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)


class Endpoint:
    """Fake gate components whose classifier can be made to fail."""

    def __init__(self) -> None:
        self.failure: Exception | None = None
        self.histories: list[list[ChatTurn]] = []
        self.personas: list[PersonaContext] = []
        self.model = "fake"

    def components(
        self, session: AsyncSession, plan_id: int, persona: PersonaContext
    ) -> TurnComponents:
        self.personas.append(persona)
        return TurnComponents(
            classifier=self, retriever=self, drafter=self, auditor=self
        )

    async def classify(
        self, message: str, history: list[ChatTurn], topics: TopicMap, session_id: str
    ) -> Classification:
        if self.failure is not None:
            raise self.failure
        self.histories.append(history)
        return Classification(category=Category.OFF_TOPIC, rationale="chat")

    async def retrieve(self, message: str, now: datetime) -> list[RetrievedNote]:
        return []

    async def noted_slugs(self, *args: object) -> frozenset[str]:
        return frozenset()

    async def draft(self, request: DraftRequest, session_id: str) -> Draft:
        return Draft(reply=f"re: {request.message}")

    async def audit(
        self,
        draft: str,
        message: str,
        history: list[ChatTurn],
        topics: TopicMap,
        now: datetime,
        session_id: str,
    ) -> AuditVerdict:
        return AuditVerdict(verdict=Verdict.PASS, rationale="fine")


@pytest.fixture
def endpoint() -> Endpoint:
    return Endpoint()


@pytest.fixture
def worker(
    sessions: async_sessionmaker[AsyncSession], endpoint: Endpoint
) -> TurnWorker:
    return TurnWorker(sessions, FixedClock(NOW), endpoint.components)


async def stage_of(session: AsyncSession, message: Message) -> str | None:
    return await session.scalar(select(Message.stage).where(Message.id == message.id))


async def reply_to(session: AsyncSession, message: Message) -> tuple[str, int] | None:
    row = await session.execute(
        select(Message.text, Message.turn_id).where(Message.reply_to_id == message.id)
    )
    found = row.first()
    return None if found is None else (found[0], found[1])


@pytest.mark.anyio
async def test_queued_messages_get_audited_replies_in_order(
    session: AsyncSession, add_course: AddCourse, worker: TurnWorker, endpoint: Endpoint
) -> None:
    plan = await add_course(3)
    first = await post_message(session, plan.user_id, "hi", NOW)
    second = await post_message(session, plan.user_id, "how's it going?", NOW)

    await worker.drain()

    assert await stage_of(session, first) == TurnStage.ANSWERED.value
    assert await stage_of(session, second) == TurnStage.ANSWERED.value
    reply = await reply_to(session, second)
    assert reply is not None and reply[0] == "re: how's it going?"
    turn = await session.scalar(select(Turn.session_id).where(Turn.id == reply[1]))
    assert turn == f"chat-{plan.user_id}"
    assert endpoint.histories[1] == [
        ChatTurn(speaker=Speaker.USER, text="hi"),
        ChatTurn(speaker=Speaker.BUDDY, text="re: hi"),
    ]
    assert endpoint.personas[0].buddy_name == "Juno"
    assert worker.available


@pytest.mark.anyio
async def test_an_unavailable_endpoint_keeps_the_message_queued(
    session: AsyncSession, add_course: AddCourse, worker: TurnWorker, endpoint: Endpoint
) -> None:
    plan = await add_course(3)
    message = await post_message(session, plan.user_id, "hi", NOW)
    endpoint.failure = LLMUnavailableError("usage limit")

    await worker.drain()

    assert await stage_of(session, message) == TurnStage.QUEUED.value
    assert await reply_to(session, message) is None
    assert not worker.available

    endpoint.failure = None
    await worker.drain()

    assert await stage_of(session, message) == TurnStage.ANSWERED.value
    assert worker.available


@pytest.mark.anyio
async def test_a_broken_turn_fails_alone(
    session: AsyncSession, add_course: AddCourse, worker: TurnWorker, endpoint: Endpoint
) -> None:
    plan = await add_course(3)
    broken = await post_message(session, plan.user_id, "hi", NOW)
    endpoint.failure = RuntimeError("bug")

    await worker.drain()
    endpoint.failure = None
    fine = await post_message(session, plan.user_id, "still there?", NOW)
    await worker.drain()

    assert await stage_of(session, broken) == TurnStage.FAILED.value
    assert await reply_to(session, broken) is None
    assert await stage_of(session, fine) == TurnStage.ANSWERED.value
