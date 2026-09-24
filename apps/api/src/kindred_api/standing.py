from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.progress import studied_slugs
from kindred_db import Plan, StudyCheckin, TopicNode
from kindred_gate import list_notes


@dataclass(frozen=True)
class Standing:
    """Where the two learners stand with each other."""

    # Days in a row the user has checked in.
    streak: int
    # Topics the buddy is ahead of the user; negative when the user is ahead.
    gap: int


def streak_length(
    checkin_days: Iterable[date], study_days: Iterable[date], today: date
) -> int:
    """Consecutive check-in days up to today. Days with no topic, like a paused day,
    are skipped rather than breaking it, and today only counts once it has a check-in,
    so it can't break the streak before it's over."""
    checked = set(checkin_days)
    planned = set(study_days)
    if not planned and not checked:
        return 0
    first = min(planned | checked)
    day = today if today in checked else today - timedelta(days=1)
    length = 0
    while day >= first:
        if day in checked:
            length += 1
        elif day in planned:
            break
        day -= timedelta(days=1)
    return length


async def load_standing(
    session: AsyncSession, plan_id: int, tz: ZoneInfo, now: datetime
) -> Standing:
    checkins = await session.scalars(
        select(StudyCheckin.at)
        .join(TopicNode, StudyCheckin.node_id == TopicNode.id)
        .where(TopicNode.plan_id == plan_id, StudyCheckin.at <= now)
    )
    days = [at.astimezone(tz).date() for at in checkins]
    start = (await session.get_one(Plan, plan_id)).start_date
    topic_days = await session.scalars(
        select(TopicNode.day).where(TopicNode.plan_id == plan_id)
    )
    study_days = [start + timedelta(days=day - 1) for day in topic_days]
    written = await list_notes(session, plan_id=plan_id, now=now)
    studied = await studied_slugs(session, plan_id, now)
    return Standing(
        streak=streak_length(days, study_days, now.astimezone(tz).date()),
        gap=len(written) - len(studied),
    )
