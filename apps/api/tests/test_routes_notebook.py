from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import Clock, FixedClock
from kindred_api.ledger import append_note
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import NoteDraft
from kindred_db import EMBEDDING_DIMENSIONS, Plan, TopicNode

AddCourse = Callable[[int], Awaitable[Plan]]
ApiClient = Callable[[Clock, TurnWorker | None], httpx.AsyncClient]
DAY_1_EVENING = datetime(2026, 10, 1, 14, 0, tzinfo=UTC)


async def write_note(session: AsyncSession, day: int, at: datetime) -> int:
    node_id = await session.scalar(select(TopicNode.id).where(TopicNode.day == day))
    assert node_id is not None
    return await append_note(
        session,
        node_id=node_id,
        note=NoteDraft(body=f"day {day} notes", shaky=["?"], sources=["https://d.t"]),
        written_at=at,
        embedding=[0.5] * EMBEDDING_DIMENSIONS,
        embedding_model="fake-embed",
    )


@pytest.mark.anyio
async def test_the_notebook_shows_written_notes_and_seals_the_rest(
    api: ApiClient, session: AsyncSession, add_course: AddCourse
) -> None:
    await add_course(3)
    await write_note(session, 1, DAY_1_EVENING)

    notebook = (await api(FixedClock(DAY_1_EVENING), None).get("/notebook")).json()

    assert [(n["topic"]["day"], n["body"]) for n in notebook["notes"]] == [
        (1, "day 1 notes")
    ]
    assert notebook["sealed"] == [
        {"day": 2, "unlocks_at": "2026-10-02T13:30:00Z"},
        {"day": 3, "unlocks_at": "2026-10-03T13:30:00Z"},
    ]


@pytest.mark.anyio
async def test_a_note_opens_only_once_it_is_visible(
    api: ApiClient, session: AsyncSession, add_course: AddCourse
) -> None:
    await add_course(2)
    later = DAY_1_EVENING + timedelta(days=1)
    note_id = await write_note(session, 2, later)
    clock = FixedClock(DAY_1_EVENING)
    client = api(clock, None)

    assert (await client.get(f"/notebook/{note_id}")).status_code == 404

    clock.set(later)
    opened = await client.get(f"/notebook/{note_id}")

    assert opened.json()["body"] == "day 2 notes"
