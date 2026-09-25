from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.chat import Thread
from kindred_contracts import Speaker, Studying, StudyTogetherCard, TurnStage
from kindred_db import Message

JOIN_TEXT = "studying with you"
# A friend doesn't text back mid-session; the buddy just acknowledges it.
REACTION = "📚"


async def join_session(
    session: AsyncSession, user_id: int, studying: Studying, now: datetime
) -> Message:
    """Body doubling: the user studies alongside the buddy's session. No turn runs."""
    card = StudyTogetherCard(
        kind="study_together", topic=studying.topic, until=studying.until
    )
    message = Message(
        user_id=user_id,
        thread=Thread.CHAT.value,
        speaker=Speaker.USER.value,
        text=JOIN_TEXT,
        at=now,
        stage=TurnStage.ANSWERED.value,
        card=card.model_dump(mode="json"),
        reaction=REACTION,
    )
    session.add(message)
    await session.flush()
    return message
