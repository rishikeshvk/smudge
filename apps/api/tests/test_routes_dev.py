from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, time, timedelta

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import Clock, FixedClock, OffsetClock, SystemClock
from kindred_api.dependencies import get_ticker
from kindred_api.dev_clock import load_offset
from kindred_api.director import RitualSchedule
from kindred_api.main import app
from kindred_api.ticker import Ticker
from kindred_api.turn_worker import TurnWorker
from kindred_db import Plan

AddPlan = Callable[[date, str], Awaitable[Plan]]
ApiClient = Callable[[Clock, TurnWorker | None], httpx.AsyncClient]

# 10:00 in Kolkata, the morning of day 1 of a plan starting 1 Oct.
REAL_NOW = datetime(2026, 10, 1, 4, 30, tzinfo=UTC)


@pytest.fixture
def client(api: ApiClient) -> httpx.AsyncClient:
    return api(OffsetClock(FixedClock(REAL_NOW), timedelta()), None)


@pytest.mark.anyio
async def test_clock_starts_at_real_time_with_no_plan(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/dev/clock")

    assert response.status_code == 200
    assert response.json() == {
        "now": "2026-10-01T04:30:00Z",
        "real_time": True,
        "day": None,
    }


@pytest.mark.anyio
async def test_advancing_moves_the_clock_and_persists_the_offset(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    response = await client.post("/dev/clock", json={"kind": "advance", "hours": 24})

    assert response.json()["now"] == "2026-10-02T04:30:00Z"
    assert response.json()["real_time"] is False
    assert await load_offset(session) == timedelta(hours=24)


@pytest.mark.anyio
async def test_jumping_to_a_day_keeps_the_local_time_of_day(
    client: httpx.AsyncClient, add_plan: AddPlan
) -> None:
    await add_plan(date(2026, 10, 1), "Asia/Kolkata")

    response = await client.post("/dev/clock", json={"kind": "jump_to_day", "day": 9})

    assert response.json()["now"] == "2026-10-09T04:30:00Z"
    assert response.json()["day"] == 9


@pytest.mark.anyio
async def test_jumping_needs_a_plan(client: httpx.AsyncClient) -> None:
    response = await client.post("/dev/clock", json={"kind": "jump_to_day", "day": 9})

    assert response.status_code == 409


@pytest.mark.anyio
async def test_back_to_real_time(
    client: httpx.AsyncClient, session: AsyncSession
) -> None:
    await client.post("/dev/clock", json={"kind": "advance", "hours": 5})

    response = await client.post("/dev/clock", json={"kind": "real_time"})

    assert response.json()["now"] == "2026-10-01T04:30:00Z"
    assert response.json()["real_time"] is True
    assert await load_offset(session) == timedelta()


@pytest.mark.anyio
async def test_time_controls_are_hidden_outside_dev_mode(api: ApiClient) -> None:
    response = await api(SystemClock(), None).get("/dev/clock")

    assert response.status_code == 404


class CountingTicker(Ticker):
    def __init__(self) -> None:
        self.ticks = 0
        self.rituals = RitualSchedule(morning=time(8), night=time(21, 30), daily_cap=4)

    async def tick(self) -> None:
        self.ticks += 1


@pytest.mark.anyio
async def test_study_now_moves_to_tonight_and_ticks(
    client: httpx.AsyncClient, add_plan: AddPlan
) -> None:
    await add_plan(date(2026, 10, 1), "Asia/Kolkata")
    ticker = CountingTicker()
    app.dependency_overrides[get_ticker] = lambda: ticker

    response = await client.post("/dev/study-now")

    # 19:00 in Kolkata on day 1.
    assert response.json()["now"] == "2026-10-01T13:30:00Z"
    assert ticker.ticks == 1


@pytest.mark.anyio
async def test_study_now_after_study_time_just_ticks(
    api: ApiClient, add_plan: AddPlan
) -> None:
    await add_plan(date(2026, 10, 1), "Asia/Kolkata")
    late = datetime(2026, 10, 1, 16, 0, tzinfo=UTC)
    ticker = CountingTicker()
    app.dependency_overrides[get_ticker] = lambda: ticker

    response = await api(OffsetClock(FixedClock(late), timedelta()), None).post(
        "/dev/study-now"
    )

    assert response.json()["now"] == "2026-10-01T16:00:00Z"
    assert ticker.ticks == 1


@pytest.mark.anyio
async def test_next_ritual_moves_to_the_next_ritual_moment_and_ticks(
    api: ApiClient, add_plan: AddPlan
) -> None:
    await add_plan(date(2026, 10, 1), "Asia/Kolkata")
    # 09:00 on day 1 in Kolkata, after the morning message.
    morning = datetime(2026, 10, 1, 3, 30, tzinfo=UTC)
    ticker = CountingTicker()
    app.dependency_overrides[get_ticker] = lambda: ticker
    client = api(OffsetClock(FixedClock(morning), timedelta()), None)

    study = (await client.post("/dev/next-ritual")).json()["now"]
    night = (await client.post("/dev/next-ritual")).json()["now"]
    tomorrow = (await client.post("/dev/next-ritual")).json()["now"]

    assert [study, night, tomorrow] == [
        "2026-10-01T13:30:00Z",
        "2026-10-01T16:00:00Z",
        "2026-10-02T02:30:00Z",
    ]
    assert ticker.ticks == 3
