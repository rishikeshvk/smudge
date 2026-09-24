from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.persona_context import load_persona_context
from kindred_contracts import PersonaContext
from kindred_db import Buddy, Plan

AddPlan = Callable[[date, str], Awaitable[Plan]]


@pytest.mark.anyio
async def test_context_puts_the_buddy_in_the_users_day(
    session: AsyncSession, add_plan: AddPlan
) -> None:
    plan = await add_plan(date(2026, 10, 1), "Asia/Kolkata")
    session.add(Buddy(user_id=plan.user_id, name="Juno"))
    await session.flush()

    # 20:00Z on 4 Oct is 01:30 on 5 Oct in Kolkata: day 5.
    context = await load_persona_context(
        session, plan.id, datetime(2026, 10, 4, 20, 0, tzinfo=UTC)
    )

    assert context == PersonaContext(
        buddy_name="Juno",
        plan_title="T",
        day=5,
        local_now=datetime(2026, 10, 5, 1, 30, tzinfo=ZoneInfo("Asia/Kolkata")),
        facts=[],
        recent_days=[],
        streak=0,
        gap=0,
    )
    assert context.local_now.utcoffset() == ZoneInfo("Asia/Kolkata").utcoffset(
        context.local_now
    )
