import argparse
import asyncio
from datetime import timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.catalog import load_curriculum
from kindred_api.clock import SystemClock
from kindred_api.config import get_settings
from kindred_api.embedding import DocumentEmbedder
from kindred_api.llm_clients import build_embedder
from kindred_api.seed import AlreadySeededError, seed_plan
from kindred_contracts import Curriculum
from kindred_db import StudyCheckin, TopicNode, User, create_engine, session_factory

# Visitors pick a plan day, not a date, so the calendar and zone only need to be fixed.
DEMO_TIMEZONE = ZoneInfo("UTC")
DEMO_BUDDY = "Juno"


async def seed_demo(
    session: AsyncSession, curriculum: Curriculum, embedder: DocumentEmbedder
) -> None:
    """The landing page's buddy: a plan with the hand-written notes, and a visitor
    who has kept up, so on any day they're level with it."""
    demo = await session.scalar(select(User).where(User.is_demo))
    if demo is None:
        demo = User(timezone=DEMO_TIMEZONE.key, is_demo=True)
        session.add(demo)
        await session.flush()
    start = SystemClock().now().astimezone(DEMO_TIMEZONE).date()
    plan = await seed_plan(
        session,
        demo,
        curriculum,
        start,
        DEMO_TIMEZONE,
        DEMO_BUDDY,
        reference_embedder=embedder,
    )
    length = timedelta(minutes=plan.session_minutes)
    nodes = await session.scalars(select(TopicNode).where(TopicNode.plan_id == plan.id))
    session.add_all(
        StudyCheckin(node_id=node.id, at=node.unlock_at + length) for node in nodes
    )
    await session.flush()


async def run(path: Path) -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        async with session_factory(engine)() as session, session.begin():
            await seed_demo(session, load_curriculum(path), build_embedder(settings))
    finally:
        await engine.dispose()
    print(f"Seeded the demo buddy {DEMO_BUDDY} on {path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the landing page's demo buddy.")
    parser.add_argument("curriculum", type=Path)
    args = parser.parse_args()
    try:
        asyncio.run(run(args.curriculum))
    except AlreadySeededError as error:
        raise SystemExit("the demo buddy is already seeded") from error


if __name__ == "__main__":
    main()
