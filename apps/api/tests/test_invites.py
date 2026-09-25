from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.auth import user_for_token
from kindred_api.invites import ALPHABET, create_invite, normalise_code, redeem
from kindred_db import User

NOW = datetime(2026, 10, 1, 3, 0, tzinfo=UTC)
WEEK = timedelta(days=7)


async def add_user(session: AsyncSession) -> User:
    user = User(timezone="UTC")
    session.add(user)
    await session.flush()
    return user


@pytest.mark.anyio
async def test_a_code_reads_well_and_signs_its_user_in(session: AsyncSession) -> None:
    user = await add_user(session)
    code = await create_invite(session, user.id, NOW, WEEK)

    token = await redeem(session, code.lower().replace("-", " "), NOW)

    assert len(code) == 9 and code[4] == "-"
    assert set(normalise_code(code)) <= set(ALPHABET)
    assert token is not None
    assert await user_for_token(session, token) == user


@pytest.mark.anyio
async def test_a_code_works_once(session: AsyncSession) -> None:
    code = await create_invite(session, (await add_user(session)).id, NOW, WEEK)

    first = await redeem(session, code, NOW)
    second = await redeem(session, code, NOW + timedelta(minutes=1))

    assert first is not None and second is None


@pytest.mark.anyio
async def test_a_code_stops_working_when_it_expires(session: AsyncSession) -> None:
    code = await create_invite(session, (await add_user(session)).id, NOW, WEEK)

    assert await redeem(session, code, NOW + WEEK) is None


@pytest.mark.anyio
async def test_an_unknown_code_signs_nobody_in(session: AsyncSession) -> None:
    await create_invite(session, (await add_user(session)).id, NOW, WEEK)

    assert await redeem(session, "ABCD-EFGH", NOW) is None
