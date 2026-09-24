from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.ledger import append_note
from kindred_api.progress import check_in
from kindred_api.standing import Standing, load_standing, streak_length
from kindred_contracts import NoteDraft
from kindred_db import EMBEDDING_DIMENSIONS, Plan, TopicNode

AddCourse = Callable[[int], Awaitable[Plan]]
KOLKATA = ZoneInfo("Asia/Kolkata")
TODAY = date(2026, 10, 5)


def test_no_check_ins_is_no_streak() -> None:
    assert streak_length([], TODAY) == 0


def test_today_counts_once_checked_in() -> None:
    days = [date(2026, 10, 3), date(2026, 10, 4), TODAY]

    assert streak_length(days, TODAY) == 3


def test_today_without_a_check_in_does_not_break_the_streak() -> None:
    assert streak_length([date(2026, 10, 3), date(2026, 10, 4)], TODAY) == 2


def test_a_missed_day_breaks_the_streak() -> None:
    assert streak_length([date(2026, 10, 2), date(2026, 10, 4), TODAY], TODAY) == 2
    assert streak_length([date(2026, 10, 3)], TODAY) == 0


def test_several_check_ins_on_one_day_count_once() -> None:
    assert streak_length([TODAY, TODAY, TODAY], TODAY) == 1


async def write_note(session: AsyncSession, day: int, at: datetime) -> None:
    node_id = await session.scalar(select(TopicNode.id).where(TopicNode.day == day))
    assert node_id is not None
    await append_note(
        session,
        node_id=node_id,
        note=NoteDraft(body=f"day {day}", shaky=["?"], sources=["https://d.t"]),
        written_at=at,
        embedding=[0.5] * EMBEDDING_DIMENSIONS,
        embedding_model="fake-embed",
    )


@pytest.mark.anyio
async def test_standing_counts_local_check_in_days_and_the_gap(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(4)
    # 20:00Z on 1 Oct is 01:30 on 2 Oct in Kolkata.
    day_2 = datetime(2026, 10, 1, 20, 0, tzinfo=UTC)
    # The evening of day 3, after its topic unlocked.
    now = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)
    for day in (1, 2, 3):
        await write_note(session, day, now - timedelta(hours=1))
    await check_in(session, plan.id, day_2)
    await check_in(session, plan.id, now)

    assert await load_standing(session, plan.id, KOLKATA, now) == Standing(
        streak=2, gap=1
    )


@pytest.mark.anyio
async def test_the_gap_goes_negative_when_the_user_is_ahead(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(3)
    now = datetime(2026, 10, 1, 10, 0, tzinfo=UTC)
    await check_in(session, plan.id, now)
    await check_in(session, plan.id, now)

    standing = await load_standing(session, plan.id, KOLKATA, now)

    assert standing.gap == -2
