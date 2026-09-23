import argparse
import asyncio
import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx2
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.catalog import load_catalog
from kindred_api.chat import post_message
from kindred_api.clock import FixedClock, SystemClock
from kindred_api.config import Settings, get_settings
from kindred_api.ingest import USER_AGENT, ingest_sources
from kindred_api.llm_runtime import LLMRuntime
from kindred_api.onboarding import accept_plan, ensure_user, onboarding_turn
from kindred_api.plans import CurrentPlan, load_current_plan
from kindred_api.progress import check_in, studied_slugs
from kindred_api.schedule import plan_moment
from kindred_api.scratch_databases import recreate_database, sibling_url
from kindred_api.ticker import Ticker
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import TopicRef, TurnTrace, Verdict
from kindred_db import (
    Message,
    RelationshipMemory,
    StudySession,
    TopicNode,
    Turn,
    create_engine,
    session_factory,
)
from kindred_gate import list_notes

TIMEZONE = ZoneInfo("Asia/Kolkata")
# 09:00 in Kolkata: onboarding happens the morning before day 1.
START = datetime(2026, 10, 1, 3, 30, tzinfo=UTC)
BUDDY_NAME = "Juno"
ONBOARDING = [
    "hi! I want to learn AWS in two weeks, maybe 3 hours a day",
    "ok, an hour a day is more realistic. let's start tomorrow and study at 19:00",
    "looks good, let's go with that",
    "yes, accept that plan",
]
# Days the simulated user skips studying, so the buddy gets ahead of them.
SKIPPED_DAYS = {4, 9}
RESULTS = Path("evals/results")


@dataclass
class Reply:
    message: str
    route: str
    fell_back: bool
    audits: list[str]
    reply: str
    # Passed an audit, or was a vetted template: invariant 5.
    audited: bool


@dataclass
class Day:
    day: int
    title: str
    studied: str | None = None
    note_words: int | None = None
    user_checked_in: bool = False
    replies: list[Reply] = field(default_factory=list)
    remembered: bool = False


@dataclass
class Report:
    started_at: str
    wall_seconds: float
    onboarding: list[str]
    days: list[Day]
    llm_calls_at_least: int
    problems: list[str]


def messages_for(day: int, topics: list[TopicRef], per_day: int) -> list[str]:
    """A day's scripted chat: an evening check on today's topic, and a morning
    message that rotates through a question about tomorrow, an earlier topic, the
    buddy itself and small talk."""
    today = topics[day - 1]
    tomorrow = topics[day] if day < len(topics) else today
    earlier = topics[max(day - 2, 0)]
    morning = [
        f"quick one before tonight: what's {tomorrow.title} about?",
        f"can you remind me what you made of {earlier.title}?",
        "are you actually an AI? and do you know what's coming later in the plan?",
        "honestly struggling to stay consistent this week",
    ][day % 4]
    evening = f"how did {today.title} go for you? anything still shaky?"
    return [evening] if per_day == 1 else [morning, evening]


async def run_simulation(settings: Settings, days: int, per_day: int) -> Report:
    started = SystemClock().now()
    url = sibling_url(settings.database_url, "sim")
    recreate_database(url)
    engine = create_engine(url)
    sessions = session_factory(engine)
    clock = FixedClock(START)
    llm = LLMRuntime(settings, settings)
    worker = TurnWorker(sessions, clock, llm.turn_components)
    ticker = Ticker(sessions, clock, llm.study, llm.memory)
    try:
        onboarding = await _onboard(sessions, clock, llm)
        plan = await _plan(sessions)
        await _ingest(sessions, plan, settings)
        topics = await _topics(sessions, plan.id)
        for day in range(1, days + 1):
            await _live_day(sessions, clock, worker, ticker, plan, day, topics, per_day)
        clock.set(plan_moment(plan.start_date, days + 1, time(9), plan.tz))
        await ticker.tick()
        report_days = await _days(sessions, plan, clock.now(), days)
    finally:
        await engine.dispose()
    return Report(
        started_at=started.isoformat(),
        wall_seconds=(SystemClock().now() - started).total_seconds(),
        onboarding=onboarding,
        days=report_days,
        llm_calls_at_least=_calls(onboarding, report_days),
        problems=problems(report_days),
    )


async def _onboard(
    sessions: async_sessionmaker[AsyncSession], clock: FixedClock, llm: LLMRuntime
) -> list[str]:
    transcript: list[str] = []
    planning = llm.planning()
    async with sessions() as session:
        user = await ensure_user(session, TIMEZONE.key)
        for text in ONBOARDING:
            clock.advance(timedelta(minutes=1))
            reply = await onboarding_turn(session, user, text, clock.now(), planning)
            await session.commit()
            transcript += [f"user: {text}", f"buddy: {reply.message.text}"]
            if reply.proposal is not None:
                await accept_plan(
                    session, user, reply.message.id, BUDDY_NAME, planning.courses
                )
                await session.commit()
                transcript.append(
                    f"accepted: {reply.proposal.title} from "
                    f"{reply.proposal.start_date} at {reply.proposal.study_time}"
                )
                return transcript
    raise SystemExit("onboarding never proposed a plan:\n" + "\n".join(transcript))


async def _plan(sessions: async_sessionmaker[AsyncSession]) -> CurrentPlan:
    async with sessions() as session:
        plan = await load_current_plan(session)
    assert plan is not None
    return plan


async def _ingest(
    sessions: async_sessionmaker[AsyncSession], plan: CurrentPlan, settings: Settings
) -> None:
    [curriculum] = [
        c
        for c in load_catalog(settings.curricula_dir)
        if c.slug == plan.curriculum_slug
    ]
    async with (
        sessions() as session,
        httpx2.AsyncClient(
            headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=30
        ) as client,
    ):
        report = await ingest_sources(
            session, plan.id, curriculum, client, SystemClock().now()
        )
        await session.commit()
    print(f"ingested {report.stored} pages; failed {len(report.failed)}", flush=True)


async def _topics(
    sessions: async_sessionmaker[AsyncSession], plan_id: int
) -> list[TopicRef]:
    async with sessions() as session:
        nodes = await session.scalars(
            select(TopicNode)
            .where(TopicNode.plan_id == plan_id)
            .order_by(TopicNode.day)
        )
        return [TopicRef(slug=n.slug, title=n.title, day=n.day) for n in nodes]


async def _live_day(
    sessions: async_sessionmaker[AsyncSession],
    clock: FixedClock,
    worker: TurnWorker,
    ticker: Ticker,
    plan: CurrentPlan,
    day: int,
    topics: list[TopicRef],
    per_day: int,
) -> None:
    """Morning chat, the buddy's study at study time, evening chat, a check-in."""
    script = messages_for(day, topics, per_day)
    morning, evening = (script[0], script[1]) if per_day > 1 else (None, script[0])
    clock.set(plan_moment(plan.start_date, day, time(9), plan.tz))
    await ticker.tick()
    if morning is not None:
        await _say(sessions, worker, plan, morning, clock)
    study_time = plan_moment(plan.start_date, day, plan.study_time, plan.tz)
    clock.set(study_time + timedelta(hours=1))
    await ticker.tick()
    await _say(sessions, worker, plan, evening, clock)
    if day not in SKIPPED_DAYS:
        clock.advance(timedelta(minutes=30))
        async with sessions() as session:
            await check_in(session, plan.id, clock.now())
            await session.commit()
    print(f"day {day} done", flush=True)


async def _say(
    sessions: async_sessionmaker[AsyncSession],
    worker: TurnWorker,
    plan: CurrentPlan,
    text: str,
    clock: FixedClock,
) -> None:
    clock.advance(timedelta(minutes=1))
    async with sessions() as session:
        await post_message(session, plan.user_id, text, clock.now())
        await session.commit()
    await worker.drain()
    if not worker.available:
        raise SystemExit("the model endpoint is unavailable; stopping the simulation")


async def _days(
    sessions: async_sessionmaker[AsyncSession],
    plan: CurrentPlan,
    now: datetime,
    days: int,
) -> list[Day]:
    async with sessions() as session:
        nodes = {
            n.day: n
            for n in await session.scalars(
                select(TopicNode).where(TopicNode.plan_id == plan.id)
            )
        }
        study = {
            s.node_id: s.status for s in await session.scalars(select(StudySession))
        }
        notes = {
            n.topic.day: n for n in await list_notes(session, plan_id=plan.id, now=now)
        }
        studied = await studied_slugs(session, plan.id, now)
        checked = {n.day for n in nodes.values() if n.slug in studied}
        remembered = {
            m.for_date for m in await session.scalars(select(RelationshipMemory))
        }
        turns = {t.id: t for t in await session.scalars(select(Turn))}
        replies = list(
            await session.scalars(
                select(Message)
                .where(Message.thread == "chat", Message.turn_id.is_not(None))
                .order_by(Message.id)
            )
        )
        result = []
        for day in range(1, days + 1):
            node = nodes[day]
            local = plan_moment(plan.start_date, day, time(12), plan.tz).astimezone(
                plan.tz
            )
            entry = Day(
                day=day,
                title=node.title,
                studied=study.get(node.id),
                note_words=len(notes[day].body.split()) if day in notes else None,
                user_checked_in=day in checked,
                remembered=local.date() in remembered,
            )
            for reply in replies:
                if reply.at.astimezone(plan.tz).date() != local.date():
                    continue
                assert reply.turn_id is not None
                trace = TurnTrace.model_validate(turns[reply.turn_id].trace)
                entry.replies.append(
                    Reply(
                        message=trace.message,
                        route=trace.directive.route.value,
                        fell_back=trace.fell_back,
                        audits=[a.audit.verdict.value for a in trace.attempts],
                        reply=trace.final_reply,
                        audited=audited(trace),
                    )
                )
            result.append(entry)
        return result


def audited(trace: TurnTrace) -> bool:
    passed = [a.reply for a in trace.attempts if a.audit.verdict is Verdict.PASS]
    return trace.fell_back or trace.final_reply in passed


def problems(days: list[Day]) -> list[str]:
    """What would make this run fail M2's "14 simulated days run end to end"."""
    found = []
    for day in days:
        if day.studied is None:
            found.append(f"day {day.day}: the buddy never sat down to study")
        if not day.replies:
            found.append(f"day {day.day}: no replies")
        if not day.remembered:
            found.append(f"day {day.day}: no memory snapshot")
        found += [
            f"day {day.day}: sent without an audit: {reply.reply!r}"
            for reply in day.replies
            if not reply.audited
        ]
    return found


def _calls(onboarding: list[str], days: list[Day]) -> int:
    # A floor: schema retries and redrafts inside the Curator aren't recorded here.
    planner = sum(1 for line in onboarding if line.startswith("buddy:")) * 2
    turns = sum(1 + 2 * len(r.audits) for d in days for r in d.replies)
    studies = sum(2 for d in days if d.studied)
    memories = sum(1 for d in days if d.remembered)
    return planner + turns + studies + memories


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run simulated days end to end through the Clock on kindred_sim."
    )
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--messages-per-day", type=int, choices=[1, 2], default=2)
    args = parser.parse_args()

    report = asyncio.run(
        run_simulation(get_settings(), args.days, args.messages_per_day)
    )

    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.fromisoformat(report.started_at).strftime("%Y%m%dT%H%M%SZ")
    path = RESULTS / f"simulate-{stamp}.json"
    path.write_text(json.dumps(asdict(report), indent=2, default=str) + "\n")
    for day in report.days:
        routes = ", ".join(
            f"{r.route}{' (fallback)' if r.fell_back else ''}" for r in day.replies
        )
        user = "✓" if day.user_checked_in else "·"
        memory = "✓" if day.remembered else "·"
        print(
            f"day {day.day:>2} {day.studied or 'not studied':<10} "
            f"{day.note_words or 0:>3} words · user {user} · memory {memory} · {routes}"
        )
    print(
        f"\n{report.wall_seconds / 60:.1f} min, at least {report.llm_calls_at_least} "
        f"LLM calls. Log: {path}"
    )
    if report.problems:
        raise SystemExit("problems:\n" + "\n".join(report.problems))


if __name__ == "__main__":
    main()
