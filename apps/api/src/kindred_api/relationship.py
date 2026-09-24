import datetime as dt
from typing import Protocol
from zoneinfo import ZoneInfo

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_contracts import (
    DayMessage,
    DaySummary,
    MemoryBrief,
    MemoryUpdate,
    Speaker,
)
from kindred_db import Buddy, Message, RelationshipMemory

RECENT_DAYS = 3


class Rememberer(Protocol):
    model: str

    async def remember(self, brief: MemoryBrief, session_id: str) -> MemoryUpdate: ...


async def unremembered_days(
    session: AsyncSession, user_id: int, tz: ZoneInfo, now: dt.datetime
) -> list[dt.date]:
    """Finished local days with chat and no memory yet, oldest first."""
    local_day = func.date(func.timezone(tz.key, Message.at))
    remembered = exists().where(
        RelationshipMemory.user_id == user_id,
        RelationshipMemory.for_date == local_day,
    )
    days = await session.scalars(
        select(local_day)
        .where(
            Message.user_id == user_id,
            Message.at <= now,
            local_day < now.astimezone(tz).date(),
            ~remembered,
        )
        .group_by(local_day)
        .order_by(local_day)
    )
    return list(days)


async def remember_day(
    session: AsyncSession,
    user_id: int,
    day: dt.date,
    tz: ZoneInfo,
    now: dt.datetime,
    writer: Rememberer,
) -> None:
    start = dt.datetime.combine(day, dt.time(), tz)
    messages = await session.scalars(
        select(Message)
        .where(
            Message.user_id == user_id,
            Message.at >= start,
            Message.at < start + dt.timedelta(days=1),
            Message.at <= now,
        )
        .order_by(Message.at, Message.id)
    )
    name = (
        await session.execute(select(Buddy.name).where(Buddy.user_id == user_id))
    ).scalar_one()
    current = await _latest(session, user_id, now)
    update = await writer.remember(
        MemoryBrief(
            buddy_name=name,
            day=day,
            conversation=[
                DayMessage(
                    speaker=Speaker(m.speaker),
                    text=m.text,
                    scheduled=m.speaker == Speaker.BUDDY and m.card is not None,
                )
                for m in messages
            ],
            facts=current.facts if current is not None else [],
        ),
        f"memory-{user_id}",
    )
    session.add(
        RelationshipMemory(
            user_id=user_id,
            for_date=day,
            summary=update.summary,
            facts=update.facts,
            written_at=now,
        )
    )
    await session.flush()


async def load_memory(
    session: AsyncSession, user_id: int, now: dt.datetime
) -> tuple[list[str], list[DaySummary]]:
    """The current facts and the last few days, as of now."""
    recent = list(
        await session.scalars(
            select(RelationshipMemory)
            .where(
                RelationshipMemory.user_id == user_id,
                RelationshipMemory.written_at <= now,
            )
            .order_by(RelationshipMemory.for_date.desc())
            .limit(RECENT_DAYS)
        )
    )
    facts = recent[0].facts if recent else []
    days = [DaySummary(day=m.for_date, summary=m.summary) for m in reversed(recent)]
    return facts, days


async def _latest(
    session: AsyncSession, user_id: int, now: dt.datetime
) -> RelationshipMemory | None:
    latest: RelationshipMemory | None = await session.scalar(
        select(RelationshipMemory)
        .where(
            RelationshipMemory.user_id == user_id,
            RelationshipMemory.written_at <= now,
        )
        .order_by(RelationshipMemory.for_date.desc())
        .limit(1)
    )
    return latest
