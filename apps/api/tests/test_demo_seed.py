from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.catalog import load_curriculum
from kindred_api.demo_seed import seed_demo
from kindred_api.seed import AlreadySeededError
from kindred_contracts import Curriculum
from kindred_db import (
    EMBEDDING_DIMENSIONS,
    Buddy,
    LedgerNote,
    Plan,
    StudyCheckin,
    TopicNode,
    User,
)

CURRICULUM = Path(__file__).parents[3] / "curricula" / "aws-2week.yaml"


class FakeEmbedder:
    model = "fake-embed"

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [[1.0] * EMBEDDING_DIMENSIONS for _ in texts]


@pytest.fixture
def curriculum() -> Curriculum:
    return load_curriculum(CURRICULUM)


@pytest.mark.anyio
async def test_the_demo_buddy_gets_its_own_user_plan_and_notes(
    session: AsyncSession, curriculum: Curriculum
) -> None:
    owner = User(timezone="UTC", is_owner=True)
    session.add(owner)
    await session.flush()

    await seed_demo(session, curriculum, FakeEmbedder())

    demo = await session.scalar(select(User).where(User.is_demo))
    assert demo is not None and demo.id != owner.id
    assert await session.scalar(select(Buddy.name).where(Buddy.user_id == demo.id))
    assert await session.scalar(select(Plan.user_id)) == demo.id
    assert await session.scalar(select(func.count(LedgerNote.id))) == sum(
        len(topic.notes) for topic in curriculum.nodes
    )


@pytest.mark.anyio
async def test_the_visitor_has_checked_in_each_day_after_the_buddy_studied(
    session: AsyncSession, curriculum: Curriculum
) -> None:
    await seed_demo(session, curriculum, FakeEmbedder())

    rows = (
        await session.execute(
            select(TopicNode.unlock_at, StudyCheckin.at).join(
                StudyCheckin, StudyCheckin.node_id == TopicNode.id
            )
        )
    ).all()
    assert len(rows) == len(curriculum.nodes)
    assert all(checked_in > unlocked for unlocked, checked_in in rows)


@pytest.mark.anyio
async def test_seeding_the_demo_twice_is_refused(
    session: AsyncSession, curriculum: Curriculum
) -> None:
    await seed_demo(session, curriculum, FakeEmbedder())

    with pytest.raises(AlreadySeededError):
        await seed_demo(session, curriculum, FakeEmbedder())
