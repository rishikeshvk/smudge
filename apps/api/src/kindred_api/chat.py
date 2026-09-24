from datetime import datetime
from enum import StrEnum

from pydantic import TypeAdapter
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.acknowledgement import reaction_to
from kindred_contracts import ChatMessage, ChatTurn, RitualCard, Speaker, TurnStage
from kindred_db import Message

HISTORY_LIMIT = 12


class Thread(StrEnum):
    CHAT = "chat"
    ONBOARDING = "onboarding"


IN_FLIGHT = [TurnStage.CLASSIFYING, TurnStage.WRITING, TurnStage.CHECKING]

CARD: TypeAdapter[RitualCard] = TypeAdapter(RitualCard)


def to_contract(message: Message) -> ChatMessage:
    return ChatMessage(
        id=message.id,
        speaker=Speaker(message.speaker),
        text=message.text,
        at=message.at,
        stage=TurnStage(message.stage) if message.stage is not None else None,
        turn_id=message.turn_id,
        card=CARD.validate_python(message.card) if message.card is not None else None,
        reaction=message.reaction,
    )


async def post_message(
    session: AsyncSession, user_id: int, text: str, now: datetime
) -> Message:
    """Queue a message for a turn, unless it's an "ok" the buddy only reacts to."""
    last = await session.scalar(
        select(Message.text)
        .where(
            Message.user_id == user_id,
            Message.thread == Thread.CHAT.value,
            Message.speaker == Speaker.BUDDY.value,
            Message.at <= now,
        )
        .order_by(Message.id.desc())
        .limit(1)
    )
    reaction = reaction_to(text, last)
    message = Message(
        user_id=user_id,
        thread=Thread.CHAT.value,
        speaker=Speaker.USER.value,
        text=text,
        at=now,
        stage=(TurnStage.QUEUED if reaction is None else TurnStage.ANSWERED).value,
        reaction=reaction,
    )
    session.add(message)
    await session.flush()
    return message


async def add_reply(
    session: AsyncSession, to: Message, text: str, turn_id: int, now: datetime
) -> Message:
    reply = Message(
        user_id=to.user_id,
        thread=to.thread,
        speaker=Speaker.BUDDY.value,
        text=text,
        at=now,
        reply_to_id=to.id,
        turn_id=turn_id,
    )
    session.add(reply)
    await session.flush()
    return reply


async def read_thread(
    session: AsyncSession,
    user_id: int,
    now: datetime,
    *,
    thread: Thread,
    before_id: int | None,
    limit: int,
) -> list[Message]:
    """The latest messages in a thread up to now, oldest first."""
    query = select(Message).where(
        Message.user_id == user_id, Message.thread == thread.value, Message.at <= now
    )
    if before_id is not None:
        query = query.where(Message.id < before_id)
    latest = await session.scalars(query.order_by(Message.id.desc()).limit(limit))
    return list(reversed(latest.all()))


async def read_reply(session: AsyncSession, message: Message) -> Message | None:
    reply: Message | None = await session.scalar(
        select(Message).where(Message.reply_to_id == message.id)
    )
    return reply


async def history_before(
    session: AsyncSession, message: Message, now: datetime
) -> list[ChatTurn]:
    """What was said before this message, including replies sent since it was queued."""
    earlier = await session.scalars(
        select(Message)
        .where(
            Message.user_id == message.user_id,
            Message.thread == message.thread,
            Message.at <= now,
            Message.id != message.id,
            or_(Message.speaker == Speaker.BUDDY.value, Message.id < message.id),
        )
        .order_by(Message.at.desc(), Message.id.desc())
        .limit(HISTORY_LIMIT)
    )
    return [
        ChatTurn(speaker=Speaker(m.speaker), text=m.text)
        for m in reversed(earlier.all())
    ]


async def next_queued(session: AsyncSession) -> Message | None:
    queued: Message | None = await session.scalar(
        select(Message)
        .where(Message.stage == TurnStage.QUEUED.value)
        .order_by(Message.id)
        .limit(1)
    )
    return queued


async def requeue_interrupted(session: AsyncSession) -> None:
    """Turns cut off by a restart start again from the queue."""
    await session.execute(
        update(Message)
        .where(Message.stage.in_([stage.value for stage in IN_FLIGHT]))
        .values(stage=TurnStage.QUEUED.value)
    )
