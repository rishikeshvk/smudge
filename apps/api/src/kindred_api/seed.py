import argparse
import asyncio
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tzlocal import get_localzone_name

from kindred_api.catalog import load_curriculum
from kindred_api.clock import SystemClock
from kindred_api.config import get_settings
from kindred_api.embedding import DocumentEmbedder
from kindred_api.llm_clients import build_embedder
from kindred_api.plans import create_plan
from kindred_contracts import Curriculum
from kindred_db import (
    Buddy,
    LedgerNote,
    NoteEmbedding,
    Plan,
    TopicNode,
    User,
    create_engine,
    session_factory,
)

# The hand-written curricula are paced for an hour a day.
SESSION_MINUTES = 60


class AlreadySeededError(Exception):
    pass


async def seed_plan(
    session: AsyncSession,
    curriculum: Curriculum,
    start_date: date,
    tz: ZoneInfo,
    buddy_name: str,
    *,
    reference_embedder: DocumentEmbedder | None,
) -> None:
    """Seed a user, their buddy and a plan. With an embedder it also stores the
    curriculum's hand-written notes, as evals do; otherwise the Curator writes them."""
    # Seeded notes can't be removed from the ledger, so never seed on top of a plan.
    if await session.scalar(select(Plan.id).limit(1)) is not None:
        raise AlreadySeededError("a plan already exists; run `make db-reset` first")

    user = User(timezone=tz.key)
    session.add(user)
    await session.flush()
    session.add(Buddy(user_id=user.id, name=buddy_name))
    plan = await create_plan(
        session,
        user.id,
        curriculum,
        start_date,
        curriculum.study_time,
        SESSION_MINUTES,
        tz,
    )
    if reference_embedder is not None:
        await _store_reference_notes(session, plan.id, curriculum, reference_embedder)


async def _store_reference_notes(
    session: AsyncSession,
    plan_id: int,
    curriculum: Curriculum,
    embedder: DocumentEmbedder,
) -> None:
    nodes = {
        node.slug: node
        for node in await session.scalars(
            select(TopicNode).where(TopicNode.plan_id == plan_id)
        )
    }
    # A note counts as written when the buddy studied the topic.
    notes = [
        (
            nodes[topic.slug],
            LedgerNote(
                node_id=nodes[topic.slug].id,
                body=note.body,
                shaky=note.shaky,
                sources=[str(url) for url in note.sources],
                written_at=nodes[topic.slug].unlock_at,
            ),
        )
        for topic in curriculum.nodes
        for note in topic.notes
    ]
    session.add_all(note for _, note in notes)
    await session.flush()

    vectors = await embedder.embed_documents(
        [f"{node.title}\n\n{note.body}" for node, note in notes]
    )
    session.add_all(
        NoteEmbedding(note_id=note.id, model=embedder.model, embedding=vector)
        for (_, note), vector in zip(notes, vectors, strict=True)
    )
    await session.flush()


async def run(
    path: Path,
    start_date: date | None,
    tz: ZoneInfo,
    buddy_name: str,
    reference_notes: bool,
) -> None:
    curriculum = load_curriculum(path)
    start = start_date or SystemClock().now().astimezone(tz).date()

    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        async with session_factory(engine)() as session, session.begin():
            await seed_plan(
                session,
                curriculum,
                start,
                tz,
                buddy_name,
                reference_embedder=build_embedder(settings)
                if reference_notes
                else None,
            )
    finally:
        await engine.dispose()

    days = len(curriculum.nodes)
    print(f"Seeded {curriculum.slug}: {days} days from {start} ({tz.key})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed a curriculum into the database.")
    parser.add_argument("curriculum", type=Path)
    parser.add_argument("--start-date", type=date.fromisoformat)
    parser.add_argument("--timezone", default=get_localzone_name())
    parser.add_argument("--buddy-name", default="Juno")
    parser.add_argument(
        "--reference-notes",
        action="store_true",
        help="store the curriculum's hand-written notes instead of letting the Curator"
        " study",
    )
    args = parser.parse_args()

    try:
        asyncio.run(
            run(
                args.curriculum,
                args.start_date,
                ZoneInfo(args.timezone),
                args.buddy_name,
                args.reference_notes,
            )
        )
    except AlreadySeededError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
