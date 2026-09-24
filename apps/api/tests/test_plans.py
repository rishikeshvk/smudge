from collections.abc import Awaitable, Callable
from datetime import date, time
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.plans import CurrentPlan, load_current_plan
from kindred_db import Plan

AddPlan = Callable[[date, str], Awaitable[Plan]]


@pytest.mark.anyio
async def test_no_plan_before_onboarding(session: AsyncSession) -> None:
    assert await load_current_plan(session) is None


@pytest.mark.anyio
async def test_current_plan_carries_the_users_timezone(
    session: AsyncSession, add_plan: AddPlan
) -> None:
    plan = await add_plan(date(2026, 10, 1), "Asia/Kolkata")

    assert await load_current_plan(session) == CurrentPlan(
        id=plan.id,
        user_id=plan.user_id,
        curriculum_slug="t",
        title="T",
        start_date=date(2026, 10, 1),
        study_time=time(19),
        session_minutes=60,
        tz=ZoneInfo("Asia/Kolkata"),
    )
