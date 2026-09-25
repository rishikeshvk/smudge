from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.chat import post_message
from kindred_api.reply_style import has_emoji, load_reply_style, reply_style
from kindred_contracts import ReplyStyle
from kindred_db import Message, Plan

AddCourse = Callable[[int], Awaitable[Plan]]
NOW = datetime(2026, 10, 2, 14, 0, tzinfo=UTC)


def test_short_messages_get_a_short_budget() -> None:
    assert reply_style(["ok", "done", "yeah"]).max_words == 12


def test_the_budget_follows_their_typical_message() -> None:
    six_words = "this part keeps confusing me honestly"

    assert reply_style([six_words, six_words, "ok"]).max_words == 15


def test_even_long_messages_get_a_bounded_reply() -> None:
    assert reply_style([" ".join(["word"] * 100)]).max_words == 70


def test_emoji_only_when_they_use_them() -> None:
    assert reply_style(["done 🎉", "ok"]).emoji
    assert not reply_style(["done", "ok"]).emoji


def test_before_any_message_the_budget_is_middling() -> None:
    assert reply_style([]) == ReplyStyle(max_words=40, emoji=False)


def test_emoji_detection_covers_the_older_symbols() -> None:
    assert has_emoji("coffee ☕")
    assert has_emoji("thanks ❤")
    assert not has_emoji("a -> b, 50% off")


@pytest.mark.anyio
async def test_only_their_latest_messages_count(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    long = " ".join(["word"] * 20)
    for n in range(3):
        await post_message(session, plan.user_id, long, NOW - timedelta(hours=n + 1))
    for n in range(5):
        await post_message(session, plan.user_id, "ok", NOW - timedelta(minutes=n))
    await post_message(session, plan.user_id, "from later 🎉", NOW + timedelta(hours=1))

    style = await load_reply_style(session, plan.user_id, NOW)

    assert style == ReplyStyle(max_words=12, emoji=False)


@pytest.mark.anyio
async def test_messages_the_app_worded_dont_count(
    session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    await post_message(session, plan.user_id, "ok", NOW)
    session.add(
        Message(
            user_id=plan.user_id,
            speaker="user",
            text="studying with you 📚 " + "word " * 30,
            at=NOW,
            card={"kind": "study_together"},
        )
    )

    style = await load_reply_style(session, plan.user_id, NOW)

    assert style == ReplyStyle(max_words=12, emoji=False)
