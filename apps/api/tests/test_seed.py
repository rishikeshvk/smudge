from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.seed import AlreadySeededError, load_curriculum, seed_plan
from kindred_contracts import Curriculum
from kindred_db import (
    EMBEDDING_DIMENSIONS,
    Buddy,
    LedgerNote,
    NoteEmbedding,
    Plan,
    TopicNode,
    TopicPrerequisite,
    TopicVocabulary,
    User,
)

CURRICULUM = """
slug: tiny
title: Tiny course
study_time: "19:00"
baseline_card: ["AWS is Amazon's cloud."]
nodes:
  - slug: first
    day: 1
    title: First topic
    audit_brief: Covers the first thing.
    vocabulary:
      - {term: first thing, kind: term}
      - {term: key, kind: term, everyday: true}
    notes:
      - body: I learned the first thing.
        shaky: [Not sure why it works.]
        sources: [https://docs.aws.amazon.com/first]
  - slug: second
    day: 2
    title: Second topic
    prerequisites: [first]
    audit_brief: Covers the second thing.
    vocabulary:
      - {term: second thing, kind: term}
    notes:
      - body: The second thing builds on the first.
        shaky: [The edge cases.]
        sources: [https://docs.aws.amazon.com/second]
"""

START = date(2026, 10, 1)
KOLKATA = ZoneInfo("Asia/Kolkata")


class FakeEmbedder:
    model = "fake-embed"

    def __init__(self) -> None:
        self.texts: list[str] = []

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.texts += texts
        return [[1.0] * EMBEDDING_DIMENSIONS for _ in texts]


@pytest.fixture
def curriculum(tmp_path: Path) -> Curriculum:
    path = tmp_path / "tiny.yaml"
    path.write_text(CURRICULUM)
    return load_curriculum(path)


@pytest.mark.anyio
async def test_seed_writes_plan_nodes_with_unlock_times(
    session: AsyncSession, curriculum: Curriculum
) -> None:
    await seed_plan(session, curriculum, START, KOLKATA, FakeEmbedder(), "Juno")

    plan = await session.scalar(select(Plan))
    assert plan is not None
    assert plan.baseline_card == ["AWS is Amazon's cloud."]

    nodes = (await session.scalars(select(TopicNode).order_by(TopicNode.day))).all()
    assert [(n.slug, n.unlock_at) for n in nodes] == [
        ("first", datetime(2026, 10, 1, 13, 30, tzinfo=UTC)),
        ("second", datetime(2026, 10, 2, 13, 30, tzinfo=UTC)),
    ]


@pytest.mark.anyio
async def test_seed_links_prerequisites_and_vocabulary(
    session: AsyncSession, curriculum: Curriculum
) -> None:
    await seed_plan(session, curriculum, START, KOLKATA, FakeEmbedder(), "Juno")
    ids = {n.slug: n.id for n in await session.scalars(select(TopicNode))}

    prerequisite = await session.scalar(select(TopicPrerequisite))
    assert prerequisite is not None
    assert (prerequisite.node_id, prerequisite.prerequisite_id) == (
        ids["second"],
        ids["first"],
    )

    everyday = await session.scalars(
        select(TopicVocabulary.term).where(TopicVocabulary.everyday)
    )
    assert everyday.all() == ["key"]


@pytest.mark.anyio
async def test_seeded_notes_are_written_when_their_topic_unlocks(
    session: AsyncSession, curriculum: Curriculum
) -> None:
    await seed_plan(session, curriculum, START, KOLKATA, FakeEmbedder(), "Juno")

    rows = await session.execute(
        select(TopicNode.slug, LedgerNote.written_at, TopicNode.unlock_at).join(
            TopicNode, LedgerNote.node_id == TopicNode.id
        )
    )
    notes = rows.all()
    assert {slug for slug, _, _ in notes} == {"first", "second"}
    assert all(written == unlock for _, written, unlock in notes)


@pytest.mark.anyio
async def test_seeding_twice_is_refused(
    session: AsyncSession, curriculum: Curriculum
) -> None:
    await seed_plan(session, curriculum, START, KOLKATA, FakeEmbedder(), "Juno")

    with pytest.raises(AlreadySeededError):
        await seed_plan(session, curriculum, START, KOLKATA, FakeEmbedder(), "Juno")


@pytest.mark.anyio
async def test_seed_embeds_each_note_with_its_topic_title(
    session: AsyncSession, curriculum: Curriculum
) -> None:
    embedder = FakeEmbedder()

    await seed_plan(session, curriculum, START, KOLKATA, embedder, "Juno")

    embeddings = (await session.scalars(select(NoteEmbedding))).all()
    assert len(embeddings) == 2
    assert {e.model for e in embeddings} == {"fake-embed"}
    assert embedder.texts[0] == "First topic\n\nI learned the first thing."


@pytest.mark.anyio
async def test_seed_gives_the_user_their_buddy(
    session: AsyncSession, curriculum: Curriculum
) -> None:
    await seed_plan(session, curriculum, START, KOLKATA, FakeEmbedder(), "Wren")

    user = await session.scalar(select(User))
    buddy = await session.scalar(select(Buddy))
    assert user is not None and buddy is not None
    assert (buddy.user_id, buddy.name) == (user.id, "Wren")
