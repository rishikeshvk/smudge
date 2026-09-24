from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_contracts import TopicRef
from kindred_db import StudyCheckin, TopicNode


async def check_in(
    session: AsyncSession, plan_id: int, now: datetime
) -> TopicRef | None:
    """Mark the user's next topic studied, in plan order; None once all are done."""
    node = await session.scalar(
        select(TopicNode)
        .outerjoin(StudyCheckin, StudyCheckin.node_id == TopicNode.id)
        .where(TopicNode.plan_id == plan_id, StudyCheckin.id.is_(None))
        .order_by(TopicNode.day)
        .limit(1)
    )
    if node is None:
        return None
    session.add(StudyCheckin(node_id=node.id, at=now))
    await session.flush()
    return TopicRef(slug=node.slug, title=node.title, day=node.day)


async def studied_slugs(
    session: AsyncSession, plan_id: int, now: datetime
) -> frozenset[str]:
    slugs = await session.scalars(
        select(TopicNode.slug)
        .join(StudyCheckin, StudyCheckin.node_id == TopicNode.id)
        .where(TopicNode.plan_id == plan_id, StudyCheckin.at <= now)
    )
    return frozenset(slugs)


async def next_topic(
    session: AsyncSession, plan_id: int, now: datetime
) -> TopicRef | None:
    """The user's next topic in plan order; None once they've done them all."""
    checked_in = StudyCheckin.node_id == TopicNode.id
    node = await session.scalar(
        select(TopicNode)
        .outerjoin(StudyCheckin, checked_in & (StudyCheckin.at <= now))
        .where(TopicNode.plan_id == plan_id, StudyCheckin.id.is_(None))
        .order_by(TopicNode.day)
        .limit(1)
    )
    if node is None:
        return None
    return TopicRef(slug=node.slug, title=node.title, day=node.day)


async def checked_in_since(
    session: AsyncSession, plan_id: int, since: datetime, now: datetime
) -> TopicRef | None:
    """The latest topic the user checked in on in a time span, if any."""
    node = await session.scalar(
        select(TopicNode)
        .join(StudyCheckin, StudyCheckin.node_id == TopicNode.id)
        .where(
            TopicNode.plan_id == plan_id,
            StudyCheckin.at >= since,
            StudyCheckin.at <= now,
        )
        .order_by(TopicNode.day.desc())
        .limit(1)
    )
    if node is None:
        return None
    return TopicRef(slug=node.slug, title=node.title, day=node.day)
