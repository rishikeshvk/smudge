from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.chat import (
    HISTORY_LIMIT,
    history_before,
    next_queued,
    post_message,
    read_thread,
    requeue_interrupted,
)
from kindred_contracts import ChatTurn, Speaker, TurnStage
from kindred_db import Message, Plan

AddCourse = Callable[[int], Awaitable[Plan]]
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)


@pytest.mark.anyio
async def test_history_is_the_latest_messages_before_this_one(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    for n in range(HISTORY_LIMIT + 2):
        await post_message(session, plan.user_id, f"m{n}", NOW)
    latest = await post_message(session, plan.user_id, "latest", NOW)

    history = await history_before(session, latest, NOW)

    assert len(history) == HISTORY_LIMIT
    assert history[0] == ChatTurn(speaker=Speaker.USER, text="m2")
    assert history[-1] == ChatTurn(speaker=Speaker.USER, text=f"m{HISTORY_LIMIT + 1}")


@pytest.mark.anyio
async def test_the_thread_never_shows_messages_from_after_now(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    await post_message(session, plan.user_id, "today", NOW)
    await post_message(session, plan.user_id, "tomorrow", NOW + timedelta(days=1))

    thread = await read_thread(session, plan.user_id, NOW, before_id=None, limit=10)

    assert [m.text for m in thread] == ["today"]


@pytest.mark.anyio
async def test_the_queue_is_oldest_first(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    first = await post_message(session, plan.user_id, "first", NOW)
    await post_message(session, plan.user_id, "second", NOW)

    assert await next_queued(session) == first


@pytest.mark.anyio
async def test_turns_cut_off_mid_way_are_queued_again(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    message = await post_message(session, plan.user_id, "hi", NOW)
    message.stage = TurnStage.WRITING.value
    await session.flush()

    await requeue_interrupted(session)

    stage = await session.scalar(select(Message.stage).where(Message.id == message.id))
    assert stage == TurnStage.QUEUED.value


@pytest.mark.anyio
async def test_history_includes_replies_sent_after_this_message_was_queued(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    first = await post_message(session, plan.user_id, "hi", NOW)
    second = await post_message(session, plan.user_id, "you there?", NOW)
    await post_message(session, plan.user_id, "hello??", NOW + timedelta(minutes=1))
    session.add(
        Message(
            user_id=plan.user_id,
            speaker="buddy",
            text="hey!",
            at=NOW + timedelta(seconds=30),
            reply_to_id=first.id,
        )
    )
    await session.flush()

    history = await history_before(session, second, NOW + timedelta(minutes=2))

    assert history == [
        ChatTurn(speaker=Speaker.USER, text="hi"),
        ChatTurn(speaker=Speaker.BUDDY, text="hey!"),
    ]
