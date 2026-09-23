from datetime import UTC, date, datetime, time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_db import (
    EMBEDDING_DIMENSIONS,
    LedgerNote,
    NoteEmbedding,
    Plan,
    TopicNode,
    User,
)
from kindred_gate import retrieve_notes

MODEL = "test-embed"
DAY_1 = datetime(2026, 10, 1, 13, 30, tzinfo=UTC)
DAY_2 = datetime(2026, 10, 2, 13, 30, tzinfo=UTC)


def axis(i: int, scale: float = 1.0) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    vector[i] = scale
    return vector


async def add_plan(session: AsyncSession) -> Plan:
    user = User(timezone="Asia/Kolkata")
    session.add(user)
    await session.flush()
    plan = Plan(
        user_id=user.id,
        curriculum_slug="test",
        title="Test",
        start_date=date(2026, 10, 1),
        study_time=time(19, 0),
        baseline_card=[],
    )
    session.add(plan)
    await session.flush()
    return plan


async def add_note(
    session: AsyncSession, plan: Plan, day: int, unlock: datetime, vector: list[float]
) -> LedgerNote:
    node = TopicNode(
        plan_id=plan.id,
        slug=f"topic-{day}",
        day=day,
        title=f"Topic {day}",
        audit_brief="Brief",
        unlock_at=unlock,
    )
    session.add(node)
    await session.flush()
    note = LedgerNote(
        node_id=node.id,
        body=f"Notes for day {day}",
        shaky=[],
        sources=[],
        written_at=unlock,
    )
    session.add(note)
    await session.flush()
    session.add(NoteEmbedding(note_id=note.id, model=MODEL, embedding=vector))
    await session.flush()
    return note


async def slugs_at(
    session: AsyncSession, plan: Plan, now: datetime, query: list[float]
) -> list[str]:
    notes = await retrieve_notes(
        session, plan_id=plan.id, query_embedding=query, model=MODEL, now=now, limit=5
    )
    return [note.topic_slug for note in notes]


@pytest.mark.anyio
async def test_a_note_stays_hidden_until_its_topic_unlocks(
    session: AsyncSession,
) -> None:
    plan = await add_plan(session)
    await add_note(session, plan, 1, DAY_1, axis(0))
    await add_note(session, plan, 2, DAY_2, axis(0))

    just_before = datetime(2026, 10, 2, 13, 29, 59, tzinfo=UTC)
    assert await slugs_at(session, plan, just_before, axis(0)) == ["topic-1"]
    assert sorted(await slugs_at(session, plan, DAY_2, axis(0))) == [
        "topic-1",
        "topic-2",
    ]


@pytest.mark.anyio
async def test_notes_come_back_nearest_first(session: AsyncSession) -> None:
    plan = await add_plan(session)
    await add_note(session, plan, 1, DAY_1, axis(0))
    await add_note(session, plan, 2, DAY_1, axis(1))

    assert await slugs_at(session, plan, DAY_2, axis(1)) == ["topic-2", "topic-1"]


@pytest.mark.anyio
async def test_other_plans_notes_never_appear(session: AsyncSession) -> None:
    mine = await add_plan(session)
    theirs = await add_plan(session)
    await add_note(session, theirs, 1, DAY_1, axis(0))

    assert await slugs_at(session, mine, DAY_2, axis(0)) == []


@pytest.mark.anyio
async def test_naive_now_is_refused(session: AsyncSession) -> None:
    plan = await add_plan(session)

    with pytest.raises(ValueError, match="timezone-aware"):
        await slugs_at(session, plan, datetime(2026, 10, 2, 19, 0), axis(0))
