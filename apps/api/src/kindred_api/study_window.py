from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_contracts import Studying, TopicRef
from kindred_db import TopicNode


async def load_studying(
    session: AsyncSession, plan_id: int, length: timedelta, now: datetime
) -> Studying | None:
    """The buddy's study session in progress: from a topic's unlock at the study time,
    for the plan's session length. The Curator writes the note when it ends."""
    node = await session.scalar(
        select(TopicNode)
        .where(
            TopicNode.plan_id == plan_id,
            TopicNode.unlock_at <= now,
            TopicNode.unlock_at > now - length,
        )
        .order_by(TopicNode.unlock_at.desc())
        .limit(1)
    )
    if node is None:
        return None
    return Studying(
        topic=TopicRef(slug=node.slug, title=node.title, day=node.day),
        until=node.unlock_at + length,
    )
