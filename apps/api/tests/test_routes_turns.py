from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import Clock, FixedClock
from kindred_api.turn_log import record_turn
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import (
    Category,
    Classification,
    Directive,
    RoleModels,
    Route,
    TurnTrace,
)
from kindred_db import Plan

AddCourse = Callable[[int], Awaitable[Plan]]
ApiClient = Callable[[Clock, TurnWorker | None], httpx.AsyncClient]
NOW = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)


@pytest.mark.anyio
async def test_a_turn_returns_its_full_trace(
    api: ApiClient, session: AsyncSession, add_course: AddCourse
) -> None:
    plan = await add_course(1)
    trace = TurnTrace(
        message="hi",
        at=NOW,
        classification=Classification(category=Category.OFF_TOPIC, rationale="chat"),
        directive=Directive(route=Route.GENERAL),
        retrieved=[],
        attempts=[],
        final_reply="hello!",
        fell_back=True,
        models=RoleModels(classifier="c", drafter="d", auditor="a"),
        latency_ms=12,
    )
    turn = await record_turn(session, trace, plan_id=plan.id, session_id="s")

    response = await api(FixedClock(NOW), None).get(f"/turns/{turn.id}")

    assert TurnTrace.model_validate(response.json()) == trace


@pytest.mark.anyio
async def test_unknown_turns_are_not_found(api: ApiClient) -> None:
    response = await api(FixedClock(NOW), None).get("/turns/999999")

    assert response.status_code == 404
