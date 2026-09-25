import logging
from datetime import datetime

import httpx2
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_db import Buddy, Message, PushToken

logger = logging.getLogger(__name__)


class ExpoTicketDetails(BaseModel):
    error: str | None = None


class ExpoTicket(BaseModel):
    status: str
    details: ExpoTicketDetails | None = None


class ExpoReply(BaseModel):
    data: list[ExpoTicket]


async def register_token(
    session: AsyncSession, user_id: int, token: str, now: datetime
) -> None:
    # A phone follows whoever signed in on it last, so no one gets another's rituals.
    statement = insert(PushToken).values(
        user_id=user_id, token=token, registered_at=now
    )
    await session.execute(
        statement.on_conflict_do_update(
            index_elements=[PushToken.token],
            set_={"user_id": user_id, "registered_at": now},
        )
    )


class Pusher:
    """Sends a buddy's rituals to its user's phones through Expo's push service."""

    def __init__(self, client: httpx2.AsyncClient, url: str) -> None:
        self._client = client
        self._url = url

    async def push(
        self, session: AsyncSession, user_id: int, messages: list[Message]
    ) -> None:
        """Best effort: a failed push is logged, and the message stays in the chat."""
        tokens = list(
            await session.scalars(
                select(PushToken.token).where(PushToken.user_id == user_id)
            )
        )
        if not tokens or not messages:
            return
        name = await session.scalar(select(Buddy.name).where(Buddy.user_id == user_id))
        notifications = [
            {
                "to": token,
                "title": name,
                "body": message.text,
                "data": {"message_id": message.id},
            }
            for message in messages
            for token in tokens
        ]
        try:
            response = await self._client.post(self._url, json=notifications)
            response.raise_for_status()
            reply = ExpoReply.model_validate_json(response.content)
        except (httpx2.HTTPError, ValueError):
            logger.warning("push failed", exc_info=True)
            return
        gone = {
            str(notification["to"])
            for notification, ticket in zip(notifications, reply.data, strict=False)
            if ticket.details is not None
            and ticket.details.error == "DeviceNotRegistered"
        }
        if gone:
            await session.execute(delete(PushToken).where(PushToken.token.in_(gone)))
            await session.commit()
