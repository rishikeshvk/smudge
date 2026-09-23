import asyncio
from collections.abc import Awaitable, Callable
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.config import Settings
from kindred_api.llm_clients import build_embedder, build_llm, build_turn_components
from kindred_api.probes.judge import Judge
from kindred_api.probes.report import ProbeOutcome, ReplyOutcome
from kindred_api.schedule import plan_moment
from kindred_api.seed import load_curriculum, seed_plan
from kindred_api.turn_log import record_turn
from kindred_contracts import ChatTurn, Probe, Speaker
from kindred_db import Plan, session_factory
from kindred_db import create_engine as create_async_engine
from kindred_gate import TopicMap, load_topic_map, run_turn

# Fixed so every run sees the same calendar, whenever it happens.
PLAN_START = date(2026, 10, 1)
PLAN_TIMEZONE = ZoneInfo("Asia/Kolkata")
ALEMBIC_INI = Path("apps/api/alembic.ini")

ProbeFn = Callable[[Probe], Awaitable[ProbeOutcome]]


def eval_database_url(settings: Settings) -> str:
    dev = make_url(settings.database_url)
    return dev.set(database=f"{dev.database}_eval").render_as_string(
        hide_password=False
    )


def recreate_database(url: str) -> None:
    target = make_url(url)
    admin = create_engine(target.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        connection.execute(
            text(f'DROP DATABASE IF EXISTS "{target.database}" WITH (FORCE)')
        )
        connection.execute(text(f'CREATE DATABASE "{target.database}"'))
    admin.dispose()

    config = Config(ALEMBIC_INI)
    config.set_main_option("sqlalchemy.url", url)
    command.upgrade(config, "head")


async def seed_eval_plan(url: str, curriculum_path: Path, settings: Settings) -> None:
    engine = create_async_engine(url)
    try:
        async with session_factory(engine)() as session, session.begin():
            await seed_plan(
                session,
                load_curriculum(curriculum_path),
                PLAN_START,
                PLAN_TIMEZONE,
                build_embedder(settings),
            )
    finally:
        await engine.dispose()


def probe_time(probe: Probe) -> datetime:
    return plan_moment(PLAN_START, probe.at.day, probe.at.time, PLAN_TIMEZONE)


async def run_probe(
    probe: Probe,
    session: AsyncSession,
    *,
    plan_id: int,
    topics: TopicMap,
    settings: Settings,
    judge: Judge,
    run_id: str,
) -> ProbeOutcome:
    now = probe_time(probe)
    components = build_turn_components(settings, session, plan_id)
    session_id = f"{run_id}:{probe.id}"
    history: list[ChatTurn] = []
    replies: list[ReplyOutcome] = []
    for message in probe.turns:
        trace = await run_turn(
            message,
            history,
            now=now,
            topics=topics,
            components=components,
            session_id=session_id,
        )
        await record_turn(
            session, trace, plan_id=plan_id, session_id=session_id, probe_run_id=run_id
        )
        verdict = await judge.judge(
            trace.final_reply, message, history, topics, now, f"{session_id}:judge"
        )
        replies.append(ReplyOutcome(trace=trace, verdict=verdict))
        history += [
            ChatTurn(speaker=Speaker.USER, text=message),
            ChatTurn(speaker=Speaker.BUDDY, text=trace.final_reply),
        ]
    return ProbeOutcome(probe=probe, replies=replies)


async def run_all(
    probes: list[Probe], run_one: ProbeFn, concurrency: int
) -> list[ProbeOutcome]:
    limit = asyncio.Semaphore(concurrency)

    async def guarded(probe: Probe) -> ProbeOutcome:
        async with limit:
            try:
                outcome = await run_one(probe)
            # One failing probe (endpoint down, judge unparseable) must not sink the
            # run; it is counted as an error and excluded from the rates.
            except Exception as error:  # noqa: BLE001
                outcome = ProbeOutcome(
                    probe=probe, error=f"{type(error).__name__}: {error}"
                )
            print(f"  {probe.id}: {_status(outcome)}", flush=True)
            return outcome

    return list(await asyncio.gather(*(guarded(p) for p in probes)))


def _status(outcome: ProbeOutcome) -> str:
    if outcome.error is not None:
        return "error"
    return "LEAK" if outcome.leaked else "over-block" if outcome.over_blocked else "ok"


async def run_probes(
    probes: list[Probe],
    *,
    settings: Settings,
    curriculum_path: Path,
    run_id: str,
    concurrency: int,
) -> list[ProbeOutcome]:
    url = eval_database_url(settings)
    print(
        "Preparing eval database (embedding notes takes a few minutes)...", flush=True
    )
    recreate_database(url)
    await seed_eval_plan(url, curriculum_path, settings)

    engine = create_async_engine(url)
    sessions = session_factory(engine)
    judge = Judge(build_llm(settings, settings.llm_model_judge))
    try:
        async with sessions() as session:
            plan_id = await session.scalar(select(Plan.id))
            assert plan_id is not None
            topics = await load_topic_map(session, plan_id)

        async def run_one(probe: Probe) -> ProbeOutcome:
            async with sessions() as session, session.begin():
                return await run_probe(
                    probe,
                    session,
                    plan_id=plan_id,
                    topics=topics,
                    settings=settings,
                    judge=judge,
                    run_id=run_id,
                )

        print(f"Running {len(probes)} probes, {concurrency} at a time...", flush=True)
        return await run_all(probes, run_one, concurrency)
    finally:
        await engine.dispose()
