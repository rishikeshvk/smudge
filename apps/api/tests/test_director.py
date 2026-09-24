from collections.abc import Awaitable, Callable
from dataclasses import replace
from datetime import UTC, datetime, time, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.director import RitualSchedule, next_ritual_at, send_due_rituals
from kindred_api.plans import CurrentPlan, load_current_plan
from kindred_api.progress import check_in
from kindred_db import Message, Plan

AddCourse = Callable[[int], Awaitable[Plan]]
AddStudy = Callable[..., Awaitable[None]]
SCHEDULE = RitualSchedule(morning=time(8), night=time(21, 30), daily_cap=4)
# Kolkata is UTC+05:30; the plan starts on 1 Oct and studies at 19:00.
KOLKATA = timedelta(hours=5, minutes=30)


def local(day: int, hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 10, day, hour, minute, tzinfo=UTC) - KOLKATA


async def current(
    session: AsyncSession, add_course: AddCourse, days: int
) -> CurrentPlan:
    await add_course(days)
    plan = await load_current_plan(session)
    assert plan is not None
    return plan


def kinds(messages: list[Message]) -> list[str | None]:
    return [None if m.card is None else str(m.card["kind"]) for m in messages]


@pytest.mark.anyio
async def test_the_morning_message_goes_out_once(
    session: AsyncSession,
    add_course: AddCourse,
) -> None:
    plan = await current(session, add_course, 3)
    await check_in(session, plan.id, local(1, 20))

    first = await send_due_rituals(session, plan, SCHEDULE, local(2, 8, 5))
    again = await send_due_rituals(session, plan, SCHEDULE, local(2, 9))

    assert kinds(first) == ["morning"] and again == []
    [message] = first
    assert "Topic 2" in message.text and "19:00" in message.text
    assert message.card is not None
    assert message.card["you"] == {"slug": "topic-2", "title": "Topic 2", "day": 2}


@pytest.mark.anyio
async def test_a_passed_window_is_skipped_not_sent_late(
    session: AsyncSession,
    add_course: AddCourse,
) -> None:
    plan = await current(session, add_course, 3)

    # A jump straight to day 2's study time: the morning is over.
    sent = await send_due_rituals(session, plan, SCHEDULE, local(2, 19, 1))

    assert sent == []


@pytest.mark.anyio
async def test_the_study_share_sends_the_curators_text_and_shaky_points(
    session: AsyncSession,
    add_course: AddCourse,
    add_study: AddStudy,
) -> None:
    plan = await current(session, add_course, 2)
    await add_study(1, local(1, 19), shaky=["why regions?"])

    [share] = await send_due_rituals(session, plan, SCHEDULE, local(1, 19, 1))

    assert share.text == "done with topic 1!"
    assert share.card is not None
    assert (share.card["kind"], share.card["shaky"]) == (
        "study_share",
        ["why regions?"],
    )


@pytest.mark.anyio
async def test_a_failed_study_is_shared_honestly(
    session: AsyncSession,
    add_course: AddCourse,
    add_study: AddStudy,
) -> None:
    plan = await current(session, add_course, 2)
    await add_study(1, local(1, 19), failed=True)

    [share] = await send_due_rituals(session, plan, SCHEDULE, local(1, 19, 1))

    assert "note I'd trust" in share.text
    assert share.card is not None and share.card["shaky"] == []


@pytest.mark.anyio
async def test_the_ask_is_about_a_topic_the_user_has_done_and_never_repeats(
    session: AsyncSession,
    add_course: AddCourse,
    add_study: AddStudy,
) -> None:
    plan = await current(session, add_course, 3)
    await add_study(1, local(1, 19), shaky=["why regions?"])
    await check_in(session, plan.id, local(1, 20))
    await add_study(2, local(2, 19), shaky=["topic 2 gap"])

    day_2 = await send_due_rituals(session, plan, SCHEDULE, local(2, 19, 1))
    await add_study(3, local(3, 19))
    day_3 = await send_due_rituals(session, plan, SCHEDULE, local(3, 19, 1))

    assert kinds(day_2) == ["study_share", "ask"]
    assert day_2[1].text.endswith("“why regions?”")
    # Day 1's only shaky point is asked already, and the user hasn't done day 2.
    assert kinds(day_3) == ["study_share"]


@pytest.mark.anyio
async def test_the_cap_drops_the_ask_before_the_night_review(
    session: AsyncSession,
    add_course: AddCourse,
    add_study: AddStudy,
) -> None:
    plan = await current(session, add_course, 2)
    await check_in(session, plan.id, local(1, 7))
    capped = RitualSchedule(morning=time(8), night=time(21, 30), daily_cap=3)

    await send_due_rituals(session, plan, capped, local(1, 8))
    await add_study(1, local(1, 19))
    evening = await send_due_rituals(session, plan, capped, local(1, 19, 1))
    night = await send_due_rituals(session, plan, capped, local(1, 21, 30))

    assert kinds(evening) == ["study_share"]
    assert kinds(night) == ["night_review"]


@pytest.mark.anyio
async def test_the_night_review_says_where_both_stand(
    session: AsyncSession,
    add_course: AddCourse,
    add_study: AddStudy,
) -> None:
    plan = await current(session, add_course, 3)
    await add_study(1, local(1, 19))
    await check_in(session, plan.id, local(1, 20))
    await add_study(2, local(2, 19))
    await check_in(session, plan.id, local(2, 20))

    sent = await send_due_rituals(session, plan, SCHEDULE, local(2, 21, 45))

    assert kinds(sent) == ["study_share", "ask", "night_review"]
    review = sent[-1]
    assert "Topic 2 is done on my side." in review.text
    assert "you did it too. that's 2 days running." in review.text
    assert review.card is not None
    assert (review.card["streak"], review.card["gap"]) == (2, 0)
    assert review.card["checked_in_today"] is True


@pytest.mark.anyio
async def test_no_rituals_outside_the_plan(
    session: AsyncSession,
    add_course: AddCourse,
) -> None:
    plan = await current(session, add_course, 2)

    before = await send_due_rituals(
        session, plan, SCHEDULE, local(1, 7) - timedelta(days=2)
    )
    after = await send_due_rituals(session, plan, SCHEDULE, local(3, 22))

    assert before == after == []


@pytest.mark.anyio
async def test_the_next_ritual_is_the_next_morning_study_or_night(
    session: AsyncSession,
    add_course: AddCourse,
) -> None:
    plan = await current(session, add_course, 2)

    assert next_ritual_at(plan, SCHEDULE, local(1, 7)) == local(1, 8)
    assert next_ritual_at(plan, SCHEDULE, local(1, 8)) == local(1, 19)
    assert next_ritual_at(plan, SCHEDULE, local(1, 19)) == local(1, 20)
    assert next_ritual_at(plan, SCHEDULE, local(1, 22)) == local(2, 8)


@pytest.mark.anyio
async def test_the_night_review_waits_for_a_long_session_to_end(
    session: AsyncSession, add_course: AddCourse, add_study: AddStudy
) -> None:
    plan = await current(session, add_course, 1)
    long = replace(plan, session_minutes=180)
    await add_study(1, local(1, 22))

    during = await send_due_rituals(session, long, SCHEDULE, local(1, 21, 45))
    after = await send_due_rituals(session, long, SCHEDULE, local(1, 22, 1))

    assert "night_review" not in kinds(during)
    assert "night_review" in kinds(after)


@pytest.mark.anyio
async def test_the_morning_says_how_a_retry_went(
    session: AsyncSession, add_course: AddCourse, add_study: AddStudy
) -> None:
    plan = await current(session, add_course, 2)
    await add_study(1, local(1, 20), failed=True)
    await add_study(1, local(2, 0, 30))

    [message] = await send_due_rituals(session, plan, SCHEDULE, local(2, 8))

    assert "had another go at Topic 1 overnight and it worked" in message.text
    assert message.text.count("Topic 2") == 1
