from datetime import UTC, date, datetime, time

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.turn_log import record_turn
from kindred_contracts import (
    Category,
    Classification,
    Directive,
    RoleModels,
    Route,
    TurnTrace,
)
from kindred_db import Plan, Turn, User


@pytest.mark.anyio
async def test_turn_is_recorded_with_its_full_trace(session: AsyncSession) -> None:
    user = User(timezone="UTC")
    session.add(user)
    await session.flush()
    plan = Plan(
        user_id=user.id,
        curriculum_slug="t",
        title="T",
        start_date=date(2026, 10, 1),
        study_time=time(19),
        baseline_card=[],
    )
    session.add(plan)
    await session.flush()
    trace = TurnTrace(
        message="hi",
        at=datetime(2026, 10, 1, 9, tzinfo=UTC),
        classification=Classification(category=Category.OFF_TOPIC, rationale="chat"),
        directive=Directive(route=Route.GENERAL),
        retrieved=[],
        attempts=[],
        final_reply="hello!",
        fell_back=True,
        models=RoleModels(classifier="c", drafter="d", auditor="a"),
        latency_ms=12,
    )

    await record_turn(session, trace, plan_id=plan.id, session_id="s", probe_run_id="r")

    turn = await session.scalar(select(Turn))
    assert turn is not None
    assert (turn.route, turn.fell_back, turn.probe_run_id) == ("general", True, "r")
    assert TurnTrace.model_validate(turn.trace) == trace
