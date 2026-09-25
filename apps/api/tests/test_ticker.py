import json
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, time, timedelta

import httpx2
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.chat import post_message
from kindred_api.clock import FixedClock
from kindred_api.director import RitualSchedule
from kindred_api.push import Pusher, register_token
from kindred_api.reflection import ReflectionComponents
from kindred_api.relationship import load_memory
from kindred_api.study import StudyComponents
from kindred_api.ticker import Ticker
from kindred_contracts import (
    AuditVerdict,
    MemoryBrief,
    MemoryUpdate,
    NoteDraft,
    Reflection,
    ReflectionBrief,
    StudyBrief,
    Verdict,
)
from kindred_db import (
    EMBEDDING_DIMENSIONS,
    Message,
    Plan,
    SourceDocument,
    StudySession,
    TopicNode,
)
from kindred_gate import TopicMap
from kindred_llm import LLMUnavailableError

NO_NETWORK = httpx2.MockTransport(lambda request: httpx2.Response(500))
AddCourse = Callable[[int], Awaitable[Plan]]
DAY_1 = datetime(2026, 10, 1, 13, 30, tzinfo=UTC)
# The buddy studies for the plan's hour, then writes its note.
DAY_1_STUDIED = DAY_1 + timedelta(hours=1)


class Buddy:
    """Fake study components."""

    model = "fake"

    def __init__(self) -> None:
        self.failure: Exception | None = None

    async def study(self, brief: StudyBrief, session_id: str) -> NoteDraft:
        if self.failure is not None:
            raise self.failure
        return NoteDraft(
            body=f"day {brief.topic.day}", shaky=["?"], sources=["u"], share="went ok"
        )

    async def audit_note(
        self, note: str, topics: TopicMap, now: datetime, session_id: str
    ) -> AuditVerdict:
        return AuditVerdict(verdict=Verdict.PASS, rationale="fine")

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.5] * EMBEDDING_DIMENSIONS for _ in texts]

    async def remember(self, brief: MemoryBrief, session_id: str) -> MemoryUpdate:
        if self.failure is not None:
            raise self.failure
        return MemoryUpdate(
            summary=f"{len(brief.conversation)} messages", facts=["likes mornings"]
        )

    async def reflect(self, brief: ReflectionBrief, session_id: str) -> Reflection:
        return Reflection(points=[])


async def sourced_course(
    session: AsyncSession, add_course: AddCourse, days: int
) -> None:
    await add_course(days)
    for node in await session.scalars(select(TopicNode)):
        session.add(
            SourceDocument(
                node_id=node.id, url="u", title="t", text="text", fetched_at=DAY_1
            )
        )
    await session.flush()


def ticker_for(
    sessions: async_sessionmaker[AsyncSession],
    clock: FixedClock,
    buddy: Buddy,
    push: httpx2.MockTransport = NO_NETWORK,
) -> Ticker:
    ticker = Ticker(
        sessions,
        clock,
        lambda: StudyComponents(curator=buddy, auditor=buddy, embedder=buddy),
        lambda: buddy,
        lambda: ReflectionComponents(reflector=buddy, auditor=buddy),
        RitualSchedule(morning=time(8), night=time(21, 30), daily_cap=4),
        Pusher(httpx2.AsyncClient(transport=push), "https://push.test"),
    )
    return ticker


async def studied_days(session: AsyncSession) -> list[int]:
    rows = await session.scalars(
        select(TopicNode.day)
        .join(StudySession, StudySession.node_id == TopicNode.id)
        .order_by(TopicNode.day)
    )
    return list(rows)


@pytest.mark.anyio
async def test_a_tick_catches_up_on_every_unlocked_topic(
    session: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    add_course: AddCourse,
) -> None:
    await sourced_course(session, add_course, 4)
    buddy = Buddy()
    # A jump to day 3's evening: days 1 to 3 are due at once.
    ticker = ticker_for(sessions, FixedClock(DAY_1_STUDIED + timedelta(days=2)), buddy)

    await ticker.tick()

    assert await studied_days(session) == [1, 2, 3]


@pytest.mark.anyio
async def test_an_unavailable_endpoint_waits_for_the_next_tick(
    session: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    add_course: AddCourse,
) -> None:
    await sourced_course(session, add_course, 2)
    buddy = Buddy()
    buddy.failure = LLMUnavailableError("usage limit")
    ticker = ticker_for(sessions, FixedClock(DAY_1_STUDIED), buddy)

    await ticker.tick()

    assert await studied_days(session) == []

    buddy.failure = None
    await ticker.tick()

    assert await studied_days(session) == [1]


@pytest.mark.anyio
async def test_a_tick_shares_what_the_buddy_just_studied(
    session: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    add_course: AddCourse,
) -> None:
    await sourced_course(session, add_course, 2)

    await ticker_for(sessions, FixedClock(DAY_1_STUDIED), Buddy()).tick()

    texts = await session.scalars(select(Message.text).where(Message.card.is_not(None)))
    assert list(texts) == ["went ok"]


@pytest.mark.anyio
async def test_a_ritual_is_pushed_to_the_phone(
    session: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    add_course: AddCourse,
) -> None:
    await sourced_course(session, add_course, 2)
    await register_token(session, "ExponentPushToken[phone]", DAY_1)
    await session.commit()
    pushed: list[str] = []

    def expo(request: httpx2.Request) -> httpx2.Response:
        pushed.extend(n["body"] for n in json.loads(request.content))
        return httpx2.Response(200, json={"data": [{"status": "ok"}]})

    ticker = ticker_for(
        sessions, FixedClock(DAY_1_STUDIED), Buddy(), httpx2.MockTransport(expo)
    )
    await ticker.tick()

    assert pushed == ["went ok"]


@pytest.mark.anyio
async def test_rituals_go_out_while_the_endpoint_is_down(
    session: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    add_course: AddCourse,
) -> None:
    await sourced_course(session, add_course, 2)
    buddy = Buddy()
    buddy.failure = LLMUnavailableError("down")
    # 08:30 in Kolkata on day 2: the morning message is due, nothing to study.
    morning = DAY_1 + timedelta(hours=13, minutes=30)

    await ticker_for(sessions, FixedClock(morning), buddy).tick()

    cards = await session.scalars(select(Message.card).where(Message.card.is_not(None)))
    assert [card["kind"] for card in cards if card is not None] == ["morning"]


@pytest.mark.anyio
async def test_nothing_happens_before_there_is_a_plan(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    await ticker_for(sessions, FixedClock(DAY_1), Buddy()).tick()


@pytest.mark.anyio
async def test_a_finished_day_of_chat_is_remembered_once(
    session: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    add_course: AddCourse,
) -> None:
    plan = await add_course(1)
    await post_message(session, plan.user_id, "morning!", DAY_1 - timedelta(hours=5))
    await post_message(session, plan.user_id, "night!", DAY_1 + timedelta(hours=3))
    next_morning = DAY_1 + timedelta(hours=14)
    buddy = Buddy()
    ticker = ticker_for(sessions, FixedClock(next_morning), buddy)

    await ticker.tick()
    await ticker.tick()

    facts, days = await load_memory(session, plan.user_id, next_morning)
    assert facts == ["likes mornings"]
    # Both messages fell on 1 Oct in Kolkata (14:00 and 22:00); 2 Oct isn't over.
    assert [(d.day, d.summary) for d in days] == [(date(2026, 10, 1), "2 messages")]
