from datetime import datetime

from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_contracts import NotebookNote, RetrievedNote, SourceExcerpt, TopicRef
from kindred_db import LedgerNote, NoteEmbedding, SourceDocument, TopicNode


def _unlocked(plan_id: int, now: datetime) -> list[ColumnElement[bool]]:
    """The gate itself: this plan's topics whose unlock time has passed, in SQL."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return [TopicNode.plan_id == plan_id, TopicNode.unlock_at <= now]


def _written(plan_id: int, now: datetime) -> list[ColumnElement[bool]]:
    return [*_unlocked(plan_id, now), LedgerNote.written_at <= now]


async def retrieve_notes(
    session: AsyncSession,
    *,
    plan_id: int,
    query_embedding: list[float],
    model: str,
    now: datetime,
    limit: int,
) -> list[RetrievedNote]:
    """Unlocked, written notes, nearest the query first."""
    distance = NoteEmbedding.embedding.cosine_distance(query_embedding).label(
        "distance"
    )
    rows = await session.execute(
        select(LedgerNote, TopicNode, distance)
        .join(TopicNode, LedgerNote.node_id == TopicNode.id)
        .join(NoteEmbedding, NoteEmbedding.note_id == LedgerNote.id)
        .where(*_written(plan_id, now), NoteEmbedding.model == model)
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


async def read_sources(
    session: AsyncSession, *, plan_id: int, node_id: int, now: datetime
) -> list[SourceExcerpt]:
    """A topic's reading material, only once the topic has unlocked."""
    documents = await session.scalars(
        select(SourceDocument)
        .join(TopicNode, SourceDocument.node_id == TopicNode.id)
        .where(*_unlocked(plan_id, now), TopicNode.id == node_id)
        .order_by(SourceDocument.id)
    )
    return [
        SourceExcerpt(url=doc.url, title=doc.title, text=doc.text) for doc in documents
    ]


async def list_notes(
    session: AsyncSession, *, plan_id: int, now: datetime
) -> list[NotebookNote]:
    """Every unlocked, written note in plan order, for the Notebook and the Curator."""
    rows = await session.execute(
        select(LedgerNote, TopicNode)
        .join(TopicNode, LedgerNote.node_id == TopicNode.id)
        .where(*_written(plan_id, now))
        .order_by(TopicNode.day, LedgerNote.id)
    )
    return [
        NotebookNote(
            note_id=note.id,
            topic=TopicRef(slug=node.slug, title=node.title, day=node.day),
            body=note.body,
            shaky=note.shaky,
            sources=note.sources,
            written_at=note.written_at,
        )
        for note, node in rows.tuples()
    ]
