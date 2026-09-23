from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import httpx
import pytest

from kindred_api.clock import Clock, FixedClock
from kindred_api.turn_worker import TurnWorker
from kindred_db import Plan

AddCourse = Callable[[int], Awaitable[Plan]]
ApiClient = Callable[[Clock, TurnWorker | None], httpx.AsyncClient]
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)


@pytest.mark.anyio
async def test_each_check_in_marks_the_next_topic(
    api: ApiClient, add_course: AddCourse
) -> None:
    await add_course(2)
    client = api(FixedClock(NOW), None)

    first = await client.post("/progress/checkins")
    second = await client.post("/progress/checkins")
    third = await client.post("/progress/checkins")

    assert first.json() == {"slug": "topic-1", "title": "Topic 1", "day": 1}
    assert second.json()["slug"] == "topic-2"
    assert third.status_code == 409


@pytest.mark.anyio
async def test_check_ins_need_a_plan(api: ApiClient) -> None:
    response = await api(FixedClock(NOW), None).post("/progress/checkins")

    assert response.status_code == 409
