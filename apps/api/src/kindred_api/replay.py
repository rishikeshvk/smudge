import argparse
import asyncio
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.accounts import AccountError, resolve_user
from kindred_api.chat import Thread, to_contract
from kindred_api.config import get_settings
from kindred_api.plans import load_current_plan
from kindred_api.schedule import plan_day
from kindred_contracts import Replay, ReplayDay, ReplayMessage, TurnTrace
from kindred_db import Buddy, Message, Turn, create_engine, session_factory
from kindred_gate import list_notes, load_topic_map


async def build_replay(session: AsyncSession, user_id: int) -> Replay:
    """Everything one user's buddy said and wrote, up to the last message."""
    plan = await load_current_plan(session, user_id)
    buddy_name = await session.scalar(
        select(Buddy.name).where(Buddy.user_id == user_id)
    )
    if plan is None or buddy_name is None:
        raise AccountError(f"user {user_id} has no buddy and plan to replay")
    # The recording ends at its last message, so notes are gated to that moment.
    end = await session.scalar(
        select(func.max(Message.at)).where(Message.user_id == user_id)
    )
    assert end is not None, "a plan is only made through the onboarding thread"
    messages = await session.scalars(
        select(Message).where(Message.user_id == user_id).order_by(Message.id)
    )
    traces = {
        turn.id: TurnTrace.model_validate(turn.trace)
        for turn in await session.scalars(select(Turn).where(Turn.plan_id == plan.id))
    }
    topics = {
        topic.day: topic.ref
        for topic in (await load_topic_map(session, plan.id)).topics
    }

    onboarding = []
    days: dict[int, list[ReplayMessage]] = {}
    for message in messages:
        if message.thread == Thread.ONBOARDING:
            onboarding.append(to_contract(message))
            continue
        trace = traces[message.turn_id] if message.turn_id is not None else None
        day = max(plan_day(plan.start_date, message.at, plan.tz), 0)
        days.setdefault(day, []).append(
            ReplayMessage(message=to_contract(message), trace=trace)
        )

    return Replay(
        buddy_name=buddy_name,
        plan_title=plan.title,
        onboarding=onboarding,
        days=[
            ReplayDay(day=day, topic=topics.get(day), messages=day_messages)
            for day, day_messages in sorted(days.items())
        ],
        notes=await list_notes(session, plan_id=plan.id, now=end),
    )


async def run(user_id: int | None, out: Path) -> int:
    engine = create_engine(get_settings().database_url)
    try:
        async with session_factory(engine)() as session:
            replay = await build_replay(session, await resolve_user(session, user_id))
    finally:
        await engine.dispose()
    out.write_text(replay.model_dump_json(indent=1) + "\n")
    return len(replay.days)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a recorded run as the landing page's replay."
    )
    parser.add_argument("--user", type=int, help="whose run; the owner by default")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        days = asyncio.run(run(args.user, args.out))
    except AccountError as error:
        raise SystemExit(str(error)) from error
    print(f"wrote {days} days to {args.out}")


if __name__ == "__main__":
    main()
