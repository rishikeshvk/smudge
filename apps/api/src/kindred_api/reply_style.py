from datetime import datetime
from statistics import median

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.chat import Thread
from kindred_contracts import ReplyStyle, Speaker
from kindred_db import Message

RECENT_MESSAGES = 5
# Before they've said anything there's nothing to match, so a middling budget.
DEFAULT_WORDS = 40
# A reply may run a bit longer than the message it answers, within sane bounds.
STRETCH = 2.5
MIN_WORDS = 12
MAX_WORDS = 70


def has_emoji(text: str) -> bool:
    # Pictographs, plus the older symbol blocks that hold ☕, ✨ and ❤.
    return any(ord(c) >= 0x1F300 or 0x2600 <= ord(c) <= 0x27BF for c in text)


def reply_style(recent: list[str]) -> ReplyStyle:
    """Match their texting: short messages get short replies, and emoji only if they
    use them."""
    if not recent:
        return ReplyStyle(max_words=DEFAULT_WORDS, emoji=False)
    words = median(len(text.split()) for text in recent)
    return ReplyStyle(
        max_words=min(max(round(STRETCH * words), MIN_WORDS), MAX_WORDS),
        emoji=any(has_emoji(text) for text in recent),
    )


async def load_reply_style(
    session: AsyncSession, user_id: int, now: datetime
) -> ReplyStyle:
    recent = await session.scalars(
        select(Message.text)
        .where(
            Message.user_id == user_id,
            Message.thread == Thread.CHAT.value,
            Message.speaker == Speaker.USER.value,
            Message.at <= now,
        )
        .order_by(Message.id.desc())
        .limit(RECENT_MESSAGES)
    )
    return reply_style(list(recent))
