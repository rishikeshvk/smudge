from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.chat import post_message
from kindred_api.clock import FixedClock
from kindred_api.relationship import load_memory
from kindred_api.study import StudyComponents
from kindred_api.ticker import Ticker
from kindred_contracts import (
    AuditVerdict,
    MemoryBrief,
    MemoryUpdate,
    NoteDraft,
    StudyBrief,
    Verdict,
)
from kindred_db import (
    EMBEDDING_DIMENSIONS,
    Plan,
    SourceDocument,
    StudySession,
    TopicNode,
)
from kindred_gate import TopicMap
from kindred_llm import LLMUnavailableError

AddCourse = Callable[[int], Awaitable[Plan]]
DAY_1 = datetime(2026, 10, 1, 13, 30, tzinfo=UTC)


class Buddy:
    """Fake study components that note whether the ticker says it's studying."""

    model = "fake"

    def __init__(self) -> None:
        self.failure: Exception | None = None
        self.ticker: Ticker | None = None
        self.studying_seen: list[bool] = []

    async def study(self, brief: StudyBrief, session_id: str) -> NoteDraft:
        if self.failure is not None:
            raise self.failure
        assert self.ticker is not None
        self.studying_seen.append(self.ticker.studying)
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
    sessions: async_sessionmaker[AsyncSession], clock: FixedClock, buddy: Buddy
) -> Ticker:
    ticker = Ticker(
        sessions,
        clock,
        lambda: StudyComponents(curator=buddy, auditor=buddy, embedder=buddy),
        lambda: buddy,
    )
    buddy.ticker = ticker
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
    ticker = ticker_for(sessions, FixedClock(DAY_1 + timedelta(days=2, hours=1)), buddy)

    await ticker.tick()

    assert await studied_days(session) == [1, 2, 3]
    assert buddy.studying_seen == [True, True, True]
    assert ticker.studying is False


@pytest.mark.anyio
async def test_an_unavailable_endpoint_waits_for_the_next_tick(
    session: AsyncSession,
    sessions: async_sessionmaker[AsyncSession],
    add_course: AddCourse,
) -> None:
    await sourced_course(session, add_course, 2)
    buddy = Buddy()
    buddy.failure = LLMUnavailableError("usage limit")
    ticker = ticker_for(sessions, FixedClock(DAY_1 + timedelta(minutes=5)), buddy)

    await ticker.tick()

    assert await studied_days(session) == []
    assert ticker.studying is False

    buddy.failure = None
    await ticker.tick()

    assert await studied_days(session) == [1]


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
