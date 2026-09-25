from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.schedule import plan_day
from kindred_api.study import StudyStatus
from kindred_contracts import Mood, MoodKind, Studying, TopicRef
from kindred_db import Plan, StudySession, TopicNode
from kindred_gate import list_notes

# Local hours the buddy counts as late.
LATE_FROM = 23
LATE_UNTIL = 6
# The most shaky points a note may have: the whole topic felt hard.
FRIED_SHAKY = 3
# How long a point the user helped sort out keeps the buddy upbeat.
UPBEAT_FOR = timedelta(hours=24)

STEADY = Mood(kind=MoodKind.STEADY, reason=None)


@dataclass(frozen=True)
class Tonight:
    """Today's topic, once the buddy has sat down with it."""

    title: str
    status: StudyStatus
    shaky: int


def mood(
    local_now: datetime,
    studying: Studying | None,
    tonight: Tonight | None,
    sorted_lately: TopicRef | None,
) -> Mood:
    """The buddy's mood comes only from its own day, never from the user's gap, streak
    or check-ins, so it can't turn into a guilt lever."""
    if studying is not None:
        return Mood(
            kind=MoodKind.FOCUSED, reason=f"mid-way through {studying.topic.title}"
        )
    if local_now.hour >= LATE_FROM or local_now.hour < LATE_UNTIL:
        return Mood(kind=MoodKind.TIRED, reason="it's late")
    if tonight is not None and tonight.status is StudyStatus.FAILED:
        return Mood(
            kind=MoodKind.FLAT, reason=f"{tonight.title} didn't come together tonight"
        )
    # Credit for sorting it out goes to the user, which is a lift, never a debt.
    if sorted_lately is not None:
        return Mood(
            kind=MoodKind.UPBEAT,
            reason=f"{sorted_lately.title} finally clicked, thanks to you",
        )
    if tonight is None:
        return STEADY
    if tonight.shaky >= FRIED_SHAKY:
        return Mood(kind=MoodKind.FRIED, reason=f"{tonight.title} was a lot")
    return STEADY


async def load_mood(
    session: AsyncSession,
    plan_id: int,
    tz: ZoneInfo,
    studying: Studying | None,
    now: datetime,
) -> Mood:
    start = (await session.get_one(Plan, plan_id)).start_date
    row = (
        await session.execute(
            select(TopicNode.title, TopicNode.slug, StudySession.status)
            .join(StudySession, StudySession.node_id == TopicNode.id)
            .where(
                TopicNode.plan_id == plan_id,
                TopicNode.day == plan_day(start, now, tz),
                StudySession.at <= now,
            )
            .order_by(StudySession.at.desc())
            .limit(1)
        )
    ).first()
    notes = await list_notes(session, plan_id=plan_id, now=now)
    tonight = None
    if row is not None:
        title, slug, status = row
        shaky = next((len(n.shaky) for n in notes if n.topic.slug == slug), 0)
        tonight = Tonight(title, StudyStatus(status), shaky)
    sorted_lately = next(
        (
            note.topic
            for note in notes
            if any(point.sorted_at > now - UPBEAT_FOR for point in note.sorted)
        ),
        None,
    )
    return mood(now.astimezone(tz), studying, tonight, sorted_lately)
