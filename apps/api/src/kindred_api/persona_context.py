from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.schedule import plan_day
from kindred_contracts import PersonaContext
from kindred_db import Buddy, Plan, User


async def load_persona_context(
    session: AsyncSession, plan_id: int, now: datetime
) -> PersonaContext:
    row = await session.execute(
        select(Plan.title, Plan.start_date, User.timezone, Buddy.name)
        .join(User, Plan.user_id == User.id)
        .join(Buddy, Buddy.user_id == User.id)
        .where(Plan.id == plan_id)
    )
    title, start_date, timezone, buddy_name = row.one()
    tz = ZoneInfo(timezone)
    return PersonaContext(
        buddy_name=buddy_name,
        plan_title=title,
        day=plan_day(start_date, now, tz),
        local_now=now.astimezone(tz),
    )
