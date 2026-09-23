from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_contracts import RetrievedNote
from kindred_db import LedgerNote, NoteEmbedding, TopicNode


async def retrieve_notes(
    session: AsyncSession,
    *,
    plan_id: int,
    query_embedding: list[float],
    model: str,
    now: datetime,
    limit: int,
) -> list[RetrievedNote]:
    """The only read of the knowledge ledger: unlocked notes, nearest first."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")

    distance = NoteEmbedding.embedding.cosine_distance(query_embedding).label(
        "distance"
    )
    rows = await session.execute(
        select(LedgerNote, TopicNode, distance)
        .join(TopicNode, LedgerNote.node_id == TopicNode.id)
        .join(NoteEmbedding, NoteEmbedding.note_id == LedgerNote.id)
        .where(
            TopicNode.plan_id == plan_id,
            TopicNode.unlock_at <= now,
            LedgerNote.written_at <= now,
            NoteEmbedding.model == model,
        )
        .order_by(distance)
        .limit(limit)
    )
    return [
        RetrievedNote(
            note_id=note.id,
            topic_slug=node.slug,
            topic_title=node.title,
            day=node.day,
            body=note.body,
            shaky=note.shaky,
            distance=note_distance,
        )
        for note, node, note_distance in rows.tuples()
    ]
