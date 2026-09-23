from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.ledger import append_note
from kindred_contracts import NoteDraft
from kindred_db import EMBEDDING_DIMENSIONS, NoteEmbedding, Plan, TopicNode
from kindred_gate import list_notes

AddCourse = Callable[[int], Awaitable[Plan]]
NOW = datetime(2026, 10, 1, 14, 0, tzinfo=UTC)


@pytest.mark.anyio
async def test_a_note_is_appended_with_its_embedding(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    node_id = await session.scalar(select(TopicNode.id))
    assert node_id is not None
    note = NoteDraft(body="IAM is who", shaky=["roles?"], sources=["https://d.test"])

    note_id = await append_note(
        session,
        node_id=node_id,
        note=note,
        written_at=NOW,
        embedding=[0.5] * EMBEDDING_DIMENSIONS,
        embedding_model="fake-embed",
    )

    [written] = await list_notes(session, plan_id=plan.id, now=NOW)
    assert (written.note_id, written.body, written.shaky) == (
        note_id,
        "IAM is who",
        ["roles?"],
    )
    model = await session.scalar(
        select(NoteEmbedding.model).where(NoteEmbedding.note_id == note_id)
    )
    assert model == "fake-embed"
