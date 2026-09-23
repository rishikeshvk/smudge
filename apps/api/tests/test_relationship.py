from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.chat import post_message
from kindred_api.relationship import load_memory, remember_day, unremembered_days
from kindred_contracts import MemoryBrief, MemoryUpdate
from kindred_db import Plan, RelationshipMemory

AddCourse = Callable[[int], Awaitable[Plan]]
KOLKATA = ZoneInfo("Asia/Kolkata")
# 23:00 on 1 Oct and 00:30 on 2 Oct in Kolkata: two local days.
LATE = datetime(2026, 10, 1, 17, 30, tzinfo=UTC)
AFTER_MIDNIGHT = datetime(2026, 10, 1, 19, 0, tzinfo=UTC)


class Writer:
    model = "fake"

    def __init__(self) -> None:
        self.briefs: list[MemoryBrief] = []

    async def remember(self, brief: MemoryBrief, session_id: str) -> MemoryUpdate:
        self.briefs.append(brief)
        return MemoryUpdate(summary=f"day {brief.day}", facts=[*brief.facts, "new"])


@pytest.mark.anyio
async def test_only_finished_local_days_with_chat_are_due(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    await post_message(session, plan.user_id, "late", LATE)
    await post_message(session, plan.user_id, "later", AFTER_MIDNIGHT)

    during_2_oct = AFTER_MIDNIGHT + timedelta(hours=1)
    after_2_oct = AFTER_MIDNIGHT + timedelta(days=1)

    assert await unremembered_days(session, plan.user_id, KOLKATA, during_2_oct) == [
        date(2026, 10, 1)
    ]
    assert await unremembered_days(session, plan.user_id, KOLKATA, after_2_oct) == [
        date(2026, 10, 1),
        date(2026, 10, 2),
    ]


@pytest.mark.anyio
async def test_a_day_is_remembered_from_its_own_messages(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    await post_message(session, plan.user_id, "late", LATE)
    await post_message(session, plan.user_id, "later", AFTER_MIDNIGHT)
    writer = Writer()
    now = AFTER_MIDNIGHT + timedelta(days=1)

    await remember_day(session, plan.user_id, date(2026, 10, 1), KOLKATA, now, writer)
    await remember_day(session, plan.user_id, date(2026, 10, 2), KOLKATA, now, writer)

    first, second = writer.briefs
    assert [t.text for t in first.conversation] == ["late"]
    assert first.buddy_name == "Juno"
    assert second.facts == ["new"]
    assert await unremembered_days(session, plan.user_id, KOLKATA, now) == []


@pytest.mark.anyio
async def test_memory_is_the_latest_facts_and_recent_days_as_of_now(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    start = datetime(2026, 10, 2, tzinfo=UTC)
    for n in range(5):
        session.add(
            RelationshipMemory(
                user_id=plan.user_id,
                for_date=date(2026, 10, 1 + n),
                summary=f"s{n}",
                facts=[f"f{n}"],
                written_at=start + timedelta(days=n),
            )
        )
    await session.flush()

    facts, days = await load_memory(session, plan.user_id, start + timedelta(days=3))

    assert facts == ["f3"]
    assert [d.summary for d in days] == ["s1", "s2", "s3"]
