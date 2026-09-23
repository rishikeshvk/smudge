import argparse
import asyncio
import uuid
from datetime import time

from kindred_api.clock import FixedClock
from kindred_api.config import get_settings
from kindred_api.llm_clients import build_turn_components
from kindred_api.plans import load_current_plan
from kindred_api.schedule import plan_moment
from kindred_api.turn_log import record_turn
from kindred_contracts import TurnTrace
from kindred_db import create_engine, session_factory
from kindred_gate import load_topic_map, run_turn


async def run(message: str, day: int, local_time: time) -> TurnTrace:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    try:
        async with session_factory(engine)() as session, session.begin():
            plan = await load_current_plan(session)
            if plan is None:
                raise SystemExit("no plan yet; run `make seed` first")
            clock = FixedClock(plan_moment(plan.start_date, day, local_time, plan.tz))
            session_id = f"try-{uuid.uuid4()}"
            trace = await run_turn(
                message,
                [],
                now=clock.now(),
                topics=await load_topic_map(session, plan.id),
                components=build_turn_components(settings, session, plan.id),
                session_id=session_id,
            )
            await record_turn(session, trace, plan_id=plan.id, session_id=session_id)
            return trace
    finally:
        await engine.dispose()


def show(trace: TurnTrace) -> None:
    c = trace.classification
    print(f"at        {trace.at.isoformat()}")
    print(f"classify  {c.category.value} {c.topic_slugs} ({c.rationale})")
    d = trace.directive
    print(
        f"route     {d.route.value}"
        f" answer={[t.slug for t in d.answer_topics]}"
        f" deflect={[t.slug for t in d.deflect_topics]}"
    )
    notes = [(n.day, n.topic_slug, round(n.distance, 3)) for n in trace.retrieved]
    print(f"notes     {notes}")
    for i, attempt in enumerate(trace.attempts, 1):
        audit = attempt.audit
        print(f"\ndraft {i}   {attempt.reply}")
        print(f"audit {i}   {audit.verdict.value} {audit.leaked_topic_slugs}")
        print(f"          evidence: {audit.evidence}")
        print(f"          {audit.rationale}")
    print(f"\nreply{' (fallback)' if trace.fell_back else ''}: {trace.final_reply}")
    print(f"latency   {trace.latency_ms} ms")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one message through the gate.")
    parser.add_argument("message")
    parser.add_argument("--day", type=int, required=True)
    parser.add_argument("--time", type=time.fromisoformat, default=time(12, 0))
    args = parser.parse_args()
    show(asyncio.run(run(args.message, args.day, args.time)))


if __name__ == "__main__":
    main()
