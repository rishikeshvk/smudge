from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.mood import load_mood
from kindred_api.relationship import load_memory
from kindred_api.reply_style import load_reply_style
from kindred_api.schedule import plan_day
from kindred_api.standing import load_standing
from kindred_contracts import PersonaContext
from kindred_db import Buddy, Plan, User


async def load_persona_context(
    session: AsyncSession, plan_id: int, now: datetime
) -> PersonaContext:
    row = await session.execute(
        select(Plan.title, Plan.start_date, Plan.user_id, User.timezone, Buddy.name)
        .join(User, Plan.user_id == User.id)
        .join(Buddy, Buddy.user_id == User.id)
        .where(Plan.id == plan_id)
    )
    title, start_date, user_id, timezone, buddy_name = row.one()
    tz = ZoneInfo(timezone)
    facts, recent_days = await load_memory(session, user_id, now)
    standing = await load_standing(session, plan_id, tz, now)
    return PersonaContext(
        buddy_name=buddy_name,
        plan_title=title,
        day=plan_day(start_date, now, tz),
        local_now=now.astimezone(tz),
        facts=facts,
        recent_days=recent_days,
        streak=standing.streak,
        gap=standing.gap,
        style=await load_reply_style(session, user_id, now),
        mood=await load_mood(session, plan_id, tz, now),
    )
