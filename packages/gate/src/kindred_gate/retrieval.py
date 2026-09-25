from datetime import datetime

from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_contracts import (
    NotebookNote,
    RetrievedNote,
    SortedPoint,
    SourceExcerpt,
    TopicRef,
)
from kindred_db import (
    LedgerNote,
    NoteEmbedding,
    ShakyResolution,
    SourceDocument,
    TopicNode,
)


def _unlocked(plan_id: int, now: datetime) -> list[ColumnElement[bool]]:
    """The gate itself: this plan's topics whose unlock time has passed, in SQL."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return [TopicNode.plan_id == plan_id, TopicNode.unlock_at <= now]


def _written(plan_id: int, now: datetime) -> list[ColumnElement[bool]]:
    return [*_unlocked(plan_id, now), LedgerNote.written_at <= now]


async def _sorted(
    session: AsyncSession, note_ids: list[int], now: datetime
) -> dict[int, list[SortedPoint]]:
    """What the user helped sort out on notes already gated, as of now."""
    resolutions = await session.scalars(
        select(ShakyResolution)
        .where(ShakyResolution.note_id.in_(note_ids), ShakyResolution.written_at <= now)
        .order_by(ShakyResolution.id)
    )
    by_note: dict[int, list[SortedPoint]] = {note_id: [] for note_id in note_ids}
    for resolution in resolutions:
        by_note[resolution.note_id].append(
            SortedPoint(
                shaky=resolution.shaky,
                insight=resolution.insight,
                sorted_at=resolution.written_at,
            )
        )
    return by_note


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
    found = rows.tuples().all()
    sorted_points = await _sorted(session, [note.id for note, _, _ in found], now)
    return [
        RetrievedNote(
            note_id=note.id,
            topic_slug=node.slug,
            topic_title=node.title,
            day=node.day,
            body=note.body,
            shaky=note.shaky,
            sorted=sorted_points[note.id],
            distance=note_distance,
        )
        for note, node, note_distance in found
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
    found = rows.tuples().all()
    sorted_points = await _sorted(session, [note.id for note, _ in found], now)
    return [
        NotebookNote(
            note_id=note.id,
            topic=TopicRef(slug=node.slug, title=node.title, day=node.day),
            body=note.body,
            shaky=note.shaky,
            sorted=sorted_points[note.id],
            sources=note.sources,
            written_at=note.written_at,
        )
        for note, node in found
    ]
