from dataclasses import dataclass
from datetime import datetime, time

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from kindred_api.chat import Thread
from kindred_api.config import Settings
from kindred_api.plans import CurrentPlan
from kindred_api.progress import checked_in_since, next_topic, studied_slugs
from kindred_api.rituals import (
    BuddyNight,
    Retried,
    RitualKind,
    RitualMessage,
    ask,
    failed_study_share,
    morning,
    night_review,
    study_share,
)
from kindred_api.schedule import plan_day, plan_moment
from kindred_api.standing import load_standing
from kindred_api.study import StudyStatus
from kindred_contracts import Speaker, TopicRef
from kindred_db import Message, Ritual, StudySession, TopicNode
from kindred_gate import list_notes


@dataclass(frozen=True)
class RitualSchedule:
    morning: time
    night: time
    # Unprompted messages a day at most.
    daily_cap: int

    @classmethod
    def from_settings(cls, settings: Settings) -> "RitualSchedule":
        return cls(
            morning=settings.morning_ritual_time,
            night=settings.night_review_time,
            daily_cap=settings.ritual_daily_cap,
        )


@dataclass(frozen=True)
class Composed:
    message: RitualMessage
    # Set on a small ask: the shaky point it asks about.
    note_id: int | None = None
    shaky: str | None = None


@dataclass(frozen=True)
class Today:
    plan: CurrentPlan
    schedule: RitualSchedule
    day: int
    topic: TopicNode
    now: datetime

    def at(self, local_time: time, day_offset: int = 0) -> datetime:
        return plan_moment(
            self.plan.start_date, self.day + day_offset, local_time, self.plan.tz
        )

    @property
    def midnight(self) -> datetime:
        return self.at(time(0), day_offset=1)

    @property
    def ref(self) -> TopicRef:
        return TopicRef(slug=self.topic.slug, title=self.topic.title, day=self.day)


async def send_due_rituals(
    session: AsyncSession, plan: CurrentPlan, schedule: RitualSchedule, now: datetime
) -> list[Message]:
    """Send whatever ritual is inside its window now and not sent yet. A window that
    has passed is skipped, so a clock jump never sends a backlog."""
    day = plan_day(plan.start_date, now, plan.tz)
    topic = await session.scalar(
        select(TopicNode).where(TopicNode.plan_id == plan.id, TopicNode.day == day)
    )
    if topic is None:
        return []
    today = Today(plan, schedule, day, topic, now)
    done = set(
        await session.scalars(
            select(Ritual.kind).where(Ritual.plan_id == plan.id, Ritual.day == day)
        )
    )
    sent: list[Message] = []
    for kind in RitualKind:
        if kind in done or not _room_for(kind, done, schedule.daily_cap):
            continue
        composed = await _compose(session, kind, today, done)
        if composed is None:
            continue
        sent.append(await _send(session, today, kind, composed))
        done.add(kind)
    return sent


def _room_for(kind: RitualKind, done: set[str], cap: int) -> bool:
    # The small ask is the first to go: it must leave room for the night review.
    reserved = kind is RitualKind.ASK and RitualKind.NIGHT_REVIEW not in done
    return len(done) + (1 if reserved else 0) < cap


async def _compose(
    session: AsyncSession, kind: RitualKind, today: Today, done: set[str]
) -> Composed | None:
    match kind:
        case RitualKind.MORNING:
            return await _morning(session, today)
        case RitualKind.STUDY_SHARE:
            return await _study_share(session, today)
        case RitualKind.ASK:
            if RitualKind.STUDY_SHARE not in done:
                return None
            return await _ask(session, today)
        case RitualKind.NIGHT_REVIEW:
            return await _night_review(session, today)


async def _morning(session: AsyncSession, today: Today) -> Composed | None:
    if (
        not today.at(today.schedule.morning)
        <= today.now
        < today.at(today.plan.study_time)
    ):
        return None
    you = await next_topic(session, today.plan.id, today.now)
    retried = await _retried(session, today)
    return Composed(morning(today.day, today.ref, you, today.plan.study_time, retried))


async def _retried(session: AsyncSession, today: Today) -> Retried | None:
    """An earlier topic studied again since midnight, after its night failed."""
    midnight = today.at(time(0))
    failed = aliased(StudySession)
    row = (
        await session.execute(
            select(TopicNode, StudySession.status)
            .join(StudySession, StudySession.node_id == TopicNode.id)
            .join(failed, failed.node_id == TopicNode.id)
            .where(
                TopicNode.plan_id == today.plan.id,
                StudySession.at >= midnight,
                StudySession.at <= today.now,
                failed.status == StudyStatus.FAILED.value,
                failed.at < midnight,
            )
            .order_by(StudySession.at.desc())
            .limit(1)
        )
    ).first()
    if row is None:
        return None
    node, status = row
    return Retried(
        TopicRef(slug=node.slug, title=node.title, day=node.day),
        worked=status == StudyStatus.WRITTEN.value,
    )


async def _study_share(session: AsyncSession, today: Today) -> Composed | None:
    study = await _tonights_study(session, today)
    if study is None or study.at < today.at(time(0)) or today.now >= today.midnight:
        return None
    if study.status == StudyStatus.FAILED.value:
        return Composed(failed_study_share(today.day, today.ref))
    notes = await list_notes(session, plan_id=today.plan.id, now=today.now)
    note = next((n for n in notes if n.note_id == study.note_id), None)
    if note is None or study.share is None:
        return None
    return Composed(study_share(today.day, today.ref, study.share, note.shaky))


async def _ask(session: AsyncSession, today: Today) -> Composed | None:
    """A shaky point from a topic the user has done too, so helping is practice."""
    if today.now >= today.midnight:
        return None
    studied = await studied_slugs(session, today.plan.id, today.now)
    asked = set(
        (
            await session.execute(
                select(Ritual.note_id, Ritual.shaky).where(
                    Ritual.plan_id == today.plan.id,
                    Ritual.kind == RitualKind.ASK.value,
                )
            )
        ).tuples()
    )
    notes = await list_notes(session, plan_id=today.plan.id, now=today.now)
    for note in reversed(notes):
        if note.topic.slug not in studied:
            continue
        for shaky in note.shaky:
            if (note.note_id, shaky) not in asked:
                return Composed(
                    ask(today.day, note.note_id, note.topic, shaky),
                    note_id=note.note_id,
                    shaky=shaky,
                )
    return None


async def _night_review(session: AsyncSession, today: Today) -> Composed | None:
    # A long session can run past the usual time; the review waits for it to end.
    start = max(
        today.at(today.schedule.night),
        today.at(today.plan.study_time) + today.plan.session_length,
    )
    if not start <= today.now < today.midnight:
        return None
    study = await _tonights_study(session, today)
    if study is None:
        night = BuddyNight.NOT_YET
    elif study.status == StudyStatus.WRITTEN.value:
        night = BuddyNight.STUDIED
    else:
        night = BuddyNight.FAILED
    you_today = await checked_in_since(
        session, today.plan.id, today.at(time(0)), today.now
    )
    standing = await load_standing(session, today.plan.id, today.plan.tz, today.now)
    return Composed(
        night_review(
            today.day, today.ref, night, you_today, standing.streak, standing.gap
        )
    )


async def _tonights_study(session: AsyncSession, today: Today) -> StudySession | None:
    study: StudySession | None = await session.scalar(
        select(StudySession)
        .where(StudySession.node_id == today.topic.id, StudySession.at <= today.now)
        .order_by(StudySession.at)
        .limit(1)
    )
    return study


async def _send(
    session: AsyncSession, today: Today, kind: RitualKind, composed: Composed
) -> Message:
    message = Message(
        user_id=today.plan.user_id,
        thread=Thread.CHAT.value,
        speaker=Speaker.BUDDY.value,
        text=composed.message.text,
        at=today.now,
        card=composed.message.card.model_dump(mode="json"),
    )
    session.add(message)
    await session.flush()
    session.add(
        Ritual(
            plan_id=today.plan.id,
            day=today.day,
            kind=kind.value,
            message_id=message.id,
            note_id=composed.note_id,
            shaky=composed.shaky,
        )
    )
    await session.flush()
    return message


def next_ritual_at(
    plan: CurrentPlan, schedule: RitualSchedule, now: datetime
) -> datetime:
    """The next moment something happens: a morning, a study session starting, its end
    (the note and its share follow) or a night review."""
    day = max(plan_day(plan.start_date, now, plan.tz), 1)
    moments = [
        moment
        for d in (day, day + 1)
        for study in [plan_moment(plan.start_date, d, plan.study_time, plan.tz)]
        for moment in (
            plan_moment(plan.start_date, d, schedule.morning, plan.tz),
            study,
            study + plan.session_length,
            plan_moment(plan.start_date, d, schedule.night, plan.tz),
        )
    ]
    return min(m for m in moments if m > now)
