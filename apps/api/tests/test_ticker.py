from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.clock import FixedClock
from kindred_api.study import StudyComponents
from kindred_api.ticker import Ticker
from kindred_contracts import AuditVerdict, NoteDraft, StudyBrief, Verdict
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
        return NoteDraft(body=f"day {brief.topic.day}", shaky=["?"], sources=["u"])

    async def audit_note(
        self, note: str, topics: TopicMap, now: datetime, session_id: str
    ) -> AuditVerdict:
        return AuditVerdict(verdict=Verdict.PASS, rationale="fine")

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[0.5] * EMBEDDING_DIMENSIONS for _ in texts]


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
        StudyComponents(curator=buddy, auditor=buddy, embedder=buddy),
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
