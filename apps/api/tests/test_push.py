import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import httpx2
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.push import Pusher, register_token
from kindred_db import Message, Plan, PushToken

AddCourse = Callable[[int], Awaitable[Plan]]
NOW = datetime(2026, 10, 1, 3, 0, tzinfo=UTC)
PHONE = "ExponentPushToken[phone]"
OLD_PHONE = "ExponentPushToken[old]"


def expo(reply: httpx2.Response) -> tuple[Pusher, list[list[dict[str, object]]]]:
    sent: list[list[dict[str, object]]] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        sent.append(json.loads(request.content))
        return reply

    client = httpx2.AsyncClient(transport=httpx2.MockTransport(handler))
    return Pusher(client, "https://push.test/send"), sent


async def ritual(session: AsyncSession, add_course: AddCourse) -> Message:
    plan = await add_course(1)
    message = Message(user_id=plan.user_id, speaker="buddy", text="morning!", at=NOW)
    session.add(message)
    await session.flush()
    return message


async def tokens(session: AsyncSession) -> list[str]:
    return list(await session.scalars(select(PushToken.token).order_by(PushToken.id)))


@pytest.mark.anyio
async def test_a_ritual_goes_to_every_phone_from_the_buddy(
    session: AsyncSession, add_course: AddCourse
) -> None:
    message = await ritual(session, add_course)
    await register_token(session, message.user_id, PHONE, NOW)
    pusher, sent = expo(httpx2.Response(200, json={"data": [{"status": "ok"}]}))

    await pusher.push(session, message.user_id, [message])

    assert sent == [
        [
            {
                "to": PHONE,
                "title": "Juno",
                "body": "morning!",
                "data": {"message_id": message.id},
            }
        ]
    ]


@pytest.mark.anyio
async def test_a_phone_that_is_gone_is_forgotten(
    session: AsyncSession, add_course: AddCourse
) -> None:
    message = await ritual(session, add_course)
    await register_token(session, message.user_id, OLD_PHONE, NOW)
    await register_token(session, message.user_id, PHONE, NOW)
    gone = {"status": "error", "details": {"error": "DeviceNotRegistered"}}
    pusher, _ = expo(httpx2.Response(200, json={"data": [gone, {"status": "ok"}]}))

    await pusher.push(session, message.user_id, [message])

    assert await tokens(session) == [PHONE]


@pytest.mark.anyio
async def test_a_failed_push_is_only_logged(
    session: AsyncSession, add_course: AddCourse
) -> None:
    message = await ritual(session, add_course)
    await register_token(session, message.user_id, PHONE, NOW)
    pusher, _ = expo(httpx2.Response(503))

    await pusher.push(session, message.user_id, [message])

    assert await tokens(session) == [PHONE]


@pytest.mark.anyio
async def test_without_phones_nothing_is_sent(
    session: AsyncSession, add_course: AddCourse
) -> None:
    message = await ritual(session, add_course)
    pusher, sent = expo(httpx2.Response(200, json={"data": []}))

    await pusher.push(session, message.user_id, [message])

    assert sent == []


@pytest.mark.anyio
async def test_a_ritual_skips_another_users_phone(
    session: AsyncSession, add_course: AddCourse
) -> None:
    message = await ritual(session, add_course)
    other = await add_course(1)
    await register_token(session, other.user_id, PHONE, NOW)
    pusher, sent = expo(httpx2.Response(200, json={"data": []}))

    await pusher.push(session, message.user_id, [message])

    assert sent == []


@pytest.mark.anyio
async def test_a_phone_follows_the_user_who_signed_in_last(
    session: AsyncSession, add_course: AddCourse
) -> None:
    first, second = await add_course(1), await add_course(1)

    await register_token(session, first.user_id, PHONE, NOW)
    await register_token(session, first.user_id, PHONE, NOW)
    await register_token(session, second.user_id, PHONE, NOW)

    assert await tokens(session) == [PHONE]
    assert list(await session.scalars(select(PushToken.user_id))) == [second.user_id]
