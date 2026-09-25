import re
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import Clock, FixedClock
from kindred_api.invites import create_invite
from kindred_api.main import app
from kindred_api.push import register_token
from kindred_api.turn_worker import TurnWorker
from kindred_db import PushToken, User

AddUser = Callable[..., Awaitable[User]]
ApiClient = Callable[[Clock, TurnWorker | None, int | None], httpx.AsyncClient]
NOW = datetime(2026, 10, 1, 3, 0, tzinfo=UTC)
WEEK = timedelta(days=7)
PUBLIC = {("GET", "/health"), ("POST", "/auth/redeem")}


@pytest.mark.anyio
async def test_a_code_trades_for_a_token_that_says_who_you_are(
    api: ApiClient, session: AsyncSession, add_user: AddUser
) -> None:
    friend = await add_user()
    code = await create_invite(session, friend.id, NOW, WEEK)
    client = api(FixedClock(NOW), None, None)

    redeemed = await client.post("/auth/redeem", json={"code": code.lower()})
    token = redeemed.json()["token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert redeemed.status_code == 200
    assert me.json() == {"is_owner": False}


@pytest.mark.anyio
async def test_a_used_or_unknown_code_does_not_work(
    api: ApiClient, session: AsyncSession, add_user: AddUser
) -> None:
    code = await create_invite(session, (await add_user()).id, NOW, WEEK)
    client = api(FixedClock(NOW), None, None)

    first = await client.post("/auth/redeem", json={"code": code})
    again = await client.post("/auth/redeem", json={"code": code})
    unknown = await client.post("/auth/redeem", json={"code": "ABCD-EFGH"})

    assert first.status_code == 200
    assert again.status_code == unknown.status_code == 404
    assert again.json() == unknown.json()


@pytest.mark.anyio
async def test_signing_out_ends_the_token_and_the_phones_pushes(
    api: ApiClient, session: AsyncSession, add_user: AddUser
) -> None:
    owner = await add_user(owner=True)
    await register_token(session, owner.id, "ExponentPushToken[phone]", NOW)
    client = api(FixedClock(NOW), None, owner.id)

    me = await client.get("/auth/me")
    out = await client.post(
        "/auth/sign-out", json={"push_token": "ExponentPushToken[phone]"}
    )
    after = await client.get("/auth/me")

    assert me.json() == {"is_owner": True}
    assert out.status_code == 204
    assert after.status_code == 401
    assert list(await session.scalars(select(PushToken.token))) == []


@pytest.mark.anyio
async def test_a_bad_token_is_turned_away(api: ApiClient) -> None:
    client = api(FixedClock(NOW), None, None)

    response = await client.get("/auth/me", headers={"Authorization": "Bearer nope"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def private_routes() -> list[tuple[str, str]]:
    return sorted(
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method in operations
        if (method.upper(), path) not in PUBLIC
    )


@pytest.mark.anyio
@pytest.mark.parametrize(("method", "path"), private_routes())
async def test_every_other_route_needs_a_signed_in_user(
    api: ApiClient, method: str, path: str
) -> None:
    client = api(FixedClock(NOW), None, None)

    response = await client.request(method, re.sub(r"\{\w+\}", "1", path), json={})

    assert response.status_code == 401
