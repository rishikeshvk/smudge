from dataclasses import dataclass
from datetime import date, time
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_db import Plan, User


@dataclass(frozen=True)
class CurrentPlan:
    id: int
    user_id: int
    start_date: date
    study_time: time
    tz: ZoneInfo


async def load_current_plan(session: AsyncSession) -> CurrentPlan | None:
    """The one plan the single hardcoded user has, if onboarding has made it."""
    row = (
        await session.execute(
            select(Plan, User.timezone)
            .join(User, Plan.user_id == User.id)
            .order_by(Plan.id)
            .limit(1)
        )
    ).first()
    if row is None:
        return None
    plan, timezone = row
    return CurrentPlan(
        id=plan.id,
        user_id=plan.user_id,
        start_date=plan.start_date,
        study_time=plan.study_time,
        tz=ZoneInfo(timezone),
    )
