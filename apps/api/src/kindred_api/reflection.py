import datetime as dt
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.ledger import append_resolution
from kindred_api.note_audit import NoteAuditor, audit_note_text
from kindred_api.plans import CurrentPlan
from kindred_contracts import (
    ChatTurn,
    Reflection,
    ReflectionBrief,
    Speaker,
    TurnTrace,
    Verdict,
)
from kindred_db import ReflectionDay, TopicNode, Turn
from kindred_gate import list_notes, load_topic_map, read_sources
from kindred_llm import StructuredOutputError


class Reflects(Protocol):
    model: str

    async def reflect(self, brief: ReflectionBrief, session_id: str) -> Reflection: ...


@dataclass(frozen=True)
class ReflectionComponents:
    reflector: Reflects
    auditor: NoteAuditor


async def unreflected_days(
    session: AsyncSession, plan: CurrentPlan, now: dt.datetime
) -> list[dt.date]:
    """Finished local days with chat turns and no reflection yet, oldest first."""
    local_day = func.date(func.timezone(plan.tz.key, Turn.at))
    reflected = exists().where(
        ReflectionDay.user_id == plan.user_id, ReflectionDay.for_date == local_day
    )
    days = await session.scalars(
        select(local_day)
        .where(
            Turn.plan_id == plan.id,
            Turn.probe_run_id.is_(None),
            Turn.at <= now,
            local_day < now.astimezone(plan.tz).date(),
            ~reflected,
        )
        .group_by(local_day)
        .order_by(local_day)
    )
    return list(days)


async def reflect_day(
    session: AsyncSession,
    plan: CurrentPlan,
    day: dt.date,
    now: dt.datetime,
    components: ReflectionComponents,
) -> int:
    """Sort out the shaky points the user explained on a finished day: each one the
    sources back up and the audit passes goes into the ledger. Returns how many."""
    exchanges = await _exchanges_by_topic(session, plan, day)
    topics = await load_topic_map(session, plan.id)
    written = 0
    for note in await list_notes(session, plan_id=plan.id, now=now):
        said = exchanges.get(note.topic.slug)
        done = {point.shaky for point in note.sorted}
        still_open = [shaky for shaky in note.shaky if shaky not in done]
        if not said or not still_open:
            continue
        node_id = await session.scalar(
            select(TopicNode.id).where(
                TopicNode.plan_id == plan.id, TopicNode.slug == note.topic.slug
            )
        )
        assert node_id is not None
        sources = await read_sources(session, plan_id=plan.id, node_id=node_id, now=now)
        if not sources:
            continue
        session_id = f"reflect-{plan.id}-{note.topic.slug}-{day}"
        try:
            reflection = await components.reflector.reflect(
                ReflectionBrief(
                    plan_title=plan.title,
                    topic=note.topic,
                    open_shaky=still_open,
                    exchanges=said,
                    sources=sources,
                ),
                f"{session_id}:reflector",
            )
        except StructuredOutputError:
            # Nothing gets sorted on output we can't trust.
            continue
        for point in reflection.points:
            if not point.sorted or point.shaky not in still_open:
                continue
            if not point.insight.strip():
                continue
            verdict = await audit_note_text(
                point.insight, topics, now, components.auditor, f"{session_id}:auditor"
            )
            if verdict.verdict is not Verdict.PASS:
                continue
            await append_resolution(
                session,
                note_id=note.note_id,
                shaky=point.shaky,
                insight=point.insight,
                written_at=now,
            )
            still_open.remove(point.shaky)
            written += 1
    session.add(ReflectionDay(user_id=plan.user_id, for_date=day, reflected_at=now))
    await session.flush()
    return written


async def _exchanges_by_topic(
    session: AsyncSession, plan: CurrentPlan, day: dt.date
) -> dict[str, list[ChatTurn]]:
    """What was said about each unlocked topic that day, from the turns' own routing."""
    start = dt.datetime.combine(day, dt.time(), plan.tz)
    turns = await session.scalars(
        select(Turn)
        .where(
            Turn.plan_id == plan.id,
            Turn.probe_run_id.is_(None),
            Turn.at >= start,
            Turn.at < start + dt.timedelta(days=1),
        )
        .order_by(Turn.at, Turn.id)
    )
    exchanges: dict[str, list[ChatTurn]] = {}
    for turn in turns:
        trace = TurnTrace.model_validate(turn.trace)
        for topic in trace.directive.answer_topics:
            exchanges.setdefault(topic.slug, []).extend(
                [
                    ChatTurn(speaker=Speaker.USER, text=trace.message),
                    ChatTurn(speaker=Speaker.BUDDY, text=trace.final_reply),
                ]
            )
    return exchanges
