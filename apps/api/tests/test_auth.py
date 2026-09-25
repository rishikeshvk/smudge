from datetime import UTC, datetime

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.auth import issue_token, revoke, sign_out, user_for_token
from kindred_db import AuthToken, PushToken, User

NOW = datetime(2026, 10, 1, 3, 0, tzinfo=UTC)


async def add_user(session: AsyncSession, *phones: str) -> User:
    user = User(timezone="UTC")
    session.add(user)
    await session.flush()
    session.add_all(
        PushToken(user_id=user.id, token=phone, registered_at=NOW) for phone in phones
    )
    await session.flush()
    return user


@pytest.mark.anyio
async def test_only_a_hash_of_the_token_is_stored(session: AsyncSession) -> None:
    user = await add_user(session)
    token = await issue_token(session, user.id, NOW)

    stored = await session.scalar(select(AuthToken.token_hash))

    assert stored is not None and token not in stored
    assert await user_for_token(session, token) == user
    assert await user_for_token(session, token + "x") is None


@pytest.mark.anyio
async def test_signing_out_ends_that_phone_only(session: AsyncSession) -> None:
    user = await add_user(session, "ExponentPushToken[a]", "ExponentPushToken[b]")
    phone_a = await issue_token(session, user.id, NOW)
    phone_b = await issue_token(session, user.id, NOW)

    await sign_out(session, user.id, phone_a, "ExponentPushToken[a]")

    assert await user_for_token(session, phone_a) is None
    assert await user_for_token(session, phone_b) == user
    assert list(await session.scalars(select(PushToken.token))) == [
        "ExponentPushToken[b]"
    ]


@pytest.mark.anyio
async def test_signing_out_leaves_another_users_phone_alone(
    session: AsyncSession,
) -> None:
    user = await add_user(session)
    other = await add_user(session, "ExponentPushToken[other]")
    token = await issue_token(session, user.id, NOW)

    await sign_out(session, user.id, token, "ExponentPushToken[other]")

    assert list(await session.scalars(select(PushToken.user_id))) == [other.id]


@pytest.mark.anyio
async def test_revoking_signs_a_user_out_everywhere(session: AsyncSession) -> None:
    user = await add_user(session, "ExponentPushToken[a]")
    other = await add_user(session, "ExponentPushToken[other]")
    tokens = [await issue_token(session, user.id, NOW) for _ in range(2)]
    kept = await issue_token(session, other.id, NOW)

    removed = await revoke(session, user.id)

    assert removed == 2
    assert [await user_for_token(session, token) for token in tokens] == [None, None]
    assert await user_for_token(session, kept) == other
    assert list(await session.scalars(select(PushToken.user_id))) == [other.id]
