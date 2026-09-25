from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import Clock, FixedClock
from kindred_api.turn_worker import TurnWorker
from kindred_db import PushToken, User

AddUser = Callable[..., Awaitable[User]]
ApiClient = Callable[[Clock, TurnWorker | None, int | None], httpx.AsyncClient]
NOW = datetime(2026, 10, 1, 3, 0, tzinfo=UTC)


@pytest.mark.anyio
async def test_a_phone_registers_for_its_user(
    api: ApiClient, session: AsyncSession, add_user: AddUser
) -> None:
    user = await add_user()
    client = api(FixedClock(NOW), None, user.id)

    ok = await client.post("/push/tokens", json={"token": "ExponentPushToken[abc]"})
    bad = await client.post("/push/tokens", json={"token": "not-a-token"})

    assert (ok.status_code, bad.status_code) == (204, 422)
    assert list(await session.execute(select(PushToken.user_id, PushToken.token))) == [
        (user.id, "ExponentPushToken[abc]")
    ]
