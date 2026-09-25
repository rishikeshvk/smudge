from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.replay import build_replay
from kindred_api.turn_log import record_turn
from kindred_contracts import (
    Category,
    Classification,
    Directive,
    RoleModels,
    Route,
    TurnTrace,
)
from kindred_db import Message, Plan

AddCourse = Callable[..., Awaitable[Plan]]
AddStudy = Callable[..., Awaitable[None]]
# 1 Oct 2026 is day 1 in Kolkata; these are 10:00 there.
DAY_0 = datetime(2026, 9, 30, 4, 30, tzinfo=UTC)
DAY_1 = datetime(2026, 10, 1, 4, 30, tzinfo=UTC)
DAY_2 = datetime(2026, 10, 2, 4, 30, tzinfo=UTC)


def say(
    user_id: int, speaker: str, text: str, at: datetime, **fields: object
) -> Message:
    return Message(user_id=user_id, speaker=speaker, text=text, at=at, **fields)


def trace_of(message: str, at: datetime) -> TurnTrace:
    return TurnTrace(
        message=message,
        at=at,
        classification=Classification(category=Category.OFF_TOPIC, rationale="chat"),
        directive=Directive(route=Route.GENERAL),
        retrieved=[],
        attempts=[],
        final_reply="hey",
        fell_back=False,
        models=RoleModels(classifier="c", drafter="d", auditor="a"),
        latency_ms=5,
    )


@pytest.mark.anyio
async def test_a_replay_groups_the_chat_by_plan_day_with_each_replys_trace(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(2)
    user = plan.user_id
    session.add(
        say(user, "buddy", "what do you want to learn?", DAY_0, thread="onboarding")
    )
    question = say(user, "user", "hi", DAY_1)
    session.add(question)
    await session.flush()
    trace = trace_of("hi", DAY_1)
    turn = await record_turn(session, trace, plan_id=plan.id, session_id="s")
    session.add_all(
        [
            say(user, "buddy", "hey", DAY_1, reply_to_id=question.id, turn_id=turn.id),
            say(user, "buddy", "morning", DAY_2),
        ]
    )
    await session.flush()

    replay = await build_replay(session, user)

    assert [m.text for m in replay.onboarding] == ["what do you want to learn?"]
    assert [(d.day, d.topic and d.topic.slug) for d in replay.days] == [
        (1, "topic-1"),
        (2, "topic-2"),
    ]
    [asked, answered] = replay.days[0].messages
    assert asked.trace is None and answered.trace == trace
    assert replay.buddy_name == "Juno"


@pytest.mark.anyio
async def test_a_replay_holds_only_the_notes_written_by_its_last_message(
    session: AsyncSession, add_course: AddCourse, add_study: AddStudy
) -> None:
    plan = await add_course(2)
    await add_study(1, datetime(2026, 10, 1, 14, 0, tzinfo=UTC), plan_id=plan.id)
    await add_study(2, datetime(2026, 10, 2, 14, 0, tzinfo=UTC), plan_id=plan.id)
    session.add(say(plan.user_id, "buddy", "morning", DAY_2))
    await session.flush()

    replay = await build_replay(session, plan.user_id)

    assert [note.topic.day for note in replay.notes] == [1]


@pytest.mark.anyio
async def test_a_replay_leaves_out_other_users_messages(
    session: AsyncSession, add_course: AddCourse
) -> None:
    mine = await add_course(1)
    theirs = await add_course(1)
    session.add_all(
        [
            say(mine.user_id, "buddy", "morning", DAY_1),
            say(theirs.user_id, "buddy", "someone else's morning", DAY_1),
        ]
    )
    await session.flush()

    replay = await build_replay(session, mine.user_id)

    assert [m.message.text for d in replay.days for m in d.messages] == ["morning"]
