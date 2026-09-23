from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from kindred_contracts import NoteDraft
from kindred_db import LedgerNote, NoteEmbedding


async def append_note(
    session: AsyncSession,
    *,
    node_id: int,
    note: NoteDraft,
    written_at: datetime,
    embedding: list[float],
    embedding_model: str,
) -> int:
    """The only writer of new knowledge; the ledger itself rejects any change."""
    row = LedgerNote(
        node_id=node_id,
        body=note.body,
        shaky=note.shaky,
        sources=note.sources,
        written_at=written_at,
    )
    session.add(row)
    await session.flush()
    session.add(
        NoteEmbedding(note_id=row.id, model=embedding_model, embedding=embedding)
    )
    await session.flush()
    return row.id
