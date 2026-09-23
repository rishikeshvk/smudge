import argparse
import asyncio
from datetime import date
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tzlocal import get_localzone_name

from kindred_api.clock import SystemClock
from kindred_api.config import get_settings
from kindred_api.embedding import DocumentEmbedder
from kindred_api.llm_clients import build_embedder
from kindred_api.schedule import plan_moment
from kindred_contracts import Curriculum
from kindred_db import (
    Buddy,
    LedgerNote,
    NoteEmbedding,
    Plan,
    TopicNode,
    TopicPrerequisite,
    TopicVocabulary,
    User,
    create_engine,
    session_factory,
)


class AlreadySeededError(Exception):
    pass


def load_curriculum(path: Path) -> Curriculum:
    return Curriculum.model_validate(yaml.safe_load(path.read_text()))


async def seed_plan(
    session: AsyncSession,
    curriculum: Curriculum,
    start_date: date,
    tz: ZoneInfo,
    embedder: DocumentEmbedder,
    buddy_name: str,
    *,
    reference_notes: bool,
) -> None:
    """Seed the plan; reference notes are the hand-written ones, kept for evals. In
    the app the Curator writes the ledger instead."""
    # Seeded notes can't be removed from the ledger, so never seed on top of a plan.
    if await session.scalar(select(Plan.id).limit(1)) is not None:
        raise AlreadySeededError("a plan already exists; run `make db-reset` first")

    user = User(timezone=tz.key)
    session.add(user)
    await session.flush()
    session.add(Buddy(user_id=user.id, name=buddy_name))

    plan = Plan(
        user_id=user.id,
        curriculum_slug=curriculum.slug,
        title=curriculum.title,
        start_date=start_date,
        study_time=curriculum.study_time,
        baseline_card=curriculum.baseline_card,
    )
    session.add(plan)
    await session.flush()

    nodes = {
        topic.slug: TopicNode(
            plan_id=plan.id,
            slug=topic.slug,
            day=topic.day,
            title=topic.title,
            audit_brief=topic.audit_brief,
            unlock_at=plan_moment(start_date, topic.day, curriculum.study_time, tz),
        )
        for topic in curriculum.nodes
    }
    session.add_all(nodes.values())
    await session.flush()

    notes: list[tuple[TopicNode, LedgerNote]] = []
    for topic in curriculum.nodes:
        node = nodes[topic.slug]
        session.add_all(
            TopicPrerequisite(node_id=node.id, prerequisite_id=nodes[slug].id)
            for slug in topic.prerequisites
        )
        session.add_all(
            TopicVocabulary(
                node_id=node.id,
                term=word.term,
                kind=word.kind.value,
                everyday=word.everyday,
            )
            for word in topic.vocabulary
        )
        # A note counts as written when the buddy studied the topic.
        notes += [
            (
                node,
                LedgerNote(
                    node_id=node.id,
                    body=note.body,
                    shaky=note.shaky,
                    sources=[str(url) for url in note.sources],
                    written_at=node.unlock_at,
                ),
            )
            for note in topic.notes
            if reference_notes
        ]
    session.add_all(note for _, note in notes)
    await session.flush()
    if not notes:
        return

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
                build_embedder(settings),
                buddy_name,
                reference_notes=reference_notes,
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
