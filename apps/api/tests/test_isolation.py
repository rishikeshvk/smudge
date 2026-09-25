"""Two users on one API: neither can read, list or act on the other's buddy, notes,
chat, traces or plan (invariant 8)."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.clock import Clock, FixedClock
from kindred_api.turn_log import record_turn
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import (
    Category,
    Classification,
    Directive,
    PersonaContext,
    RoleModels,
    Route,
    TurnTrace,
)
from kindred_db import Buddy, Message, Plan
from kindred_gate import TurnComponents, list_notes

AddCourse = Callable[..., Awaitable[Plan]]
AddStudy = Callable[..., Awaitable[None]]
ApiClient = Callable[[Clock, TurnWorker | None, int | None], httpx.AsyncClient]
# Day 1's topic was studied at 19:00-20:00 in Kolkata; this is the next morning.
STUDIED = datetime(2026, 10, 1, 14, 30, tzinfo=UTC)
NOW = datetime(2026, 10, 2, 3, 0, tzinfo=UTC)


@dataclass(frozen=True)
class Learner:
    plan: Plan
    note_id: int
    message_id: int
    turn_id: int


async def learner(
    session: AsyncSession,
    add_course: AddCourse,
    add_study: AddStudy,
    name: str,
) -> Learner:
    plan = await add_course(3)
    buddy = await session.scalar(select(Buddy).where(Buddy.user_id == plan.user_id))
    assert buddy is not None
    buddy.name = name
    await add_study(1, STUDIED, shaky=[f"{name}'s shaky point"], plan_id=plan.id)
    [note] = await list_notes(session, plan_id=plan.id, now=NOW)
    message = Message(user_id=plan.user_id, speaker="user", text=f"hi {name}", at=NOW)
    session.add(message)
    trace = TurnTrace(
        message=f"hi {name}",
        at=NOW,
        classification=Classification(category=Category.OFF_TOPIC, rationale="chat"),
        directive=Directive(route=Route.GENERAL),
        retrieved=[],
        attempts=[],
        final_reply=f"hey, {name} here",
        fell_back=False,
        models=RoleModels(classifier="c", drafter="d", auditor="a"),
        latency_ms=1,
    )
    turn = await record_turn(session, trace, plan_id=plan.id, session_id=name)
    await session.flush()
    return Learner(plan, note.note_id, message.id, turn.id)


def unused(
    session: AsyncSession, plan_id: int, persona: PersonaContext
) -> TurnComponents:
    raise AssertionError("nothing drains the queue in these tests")


@pytest.fixture
def worker(sessions: async_sessionmaker[AsyncSession]) -> TurnWorker:
    return TurnWorker(sessions, FixedClock(NOW), unused)


@pytest.fixture
async def pair(
    session: AsyncSession, add_course: AddCourse, add_study: AddStudy
) -> tuple[Learner, Learner]:
    return (
        await learner(session, add_course, add_study, "Juno"),
        await learner(session, add_course, add_study, "Sol"),
    )


@pytest.mark.anyio
async def test_each_user_lists_only_their_own(
    api: ApiClient, worker: TurnWorker, pair: tuple[Learner, Learner]
) -> None:
    for me, name in zip(pair, ["Juno", "Sol"], strict=True):
        client = api(FixedClock(NOW), worker, me.plan.user_id)

        buddy = (await client.get("/buddy")).json()
        chat = (await client.get("/chat/messages")).json()
        notebook = (await client.get("/notebook")).json()

        assert buddy["name"] == name
        assert [m["text"] for m in chat] == [f"hi {name}"]
        assert [n["note_id"] for n in notebook["notes"]] == [me.note_id]
        assert notebook["notes"][0]["shaky"] == [f"{name}'s shaky point"]


@pytest.mark.anyio
async def test_another_users_rows_are_not_found(
    api: ApiClient, pair: tuple[Learner, Learner]
) -> None:
    me, them = pair
    client = api(FixedClock(NOW), None, me.plan.user_id)

    mine = [
        await client.get(f"/notebook/{me.note_id}"),
        await client.get(f"/chat/messages/{me.message_id}"),
        await client.get(f"/turns/{me.turn_id}"),
    ]
    theirs = [
        await client.get(f"/notebook/{them.note_id}"),
        await client.get(f"/chat/messages/{them.message_id}"),
        await client.get(f"/turns/{them.turn_id}"),
    ]

    assert [r.status_code for r in mine] == [200, 200, 200]
    assert [r.status_code for r in theirs] == [404, 404, 404]
    assert "Sol" not in "".join(r.text for r in theirs)


@pytest.mark.anyio
async def test_acting_changes_only_your_own_plan(
    api: ApiClient, worker: TurnWorker, pair: tuple[Learner, Learner]
) -> None:
    me, them = pair
    mine = api(FixedClock(NOW), worker, me.plan.user_id)
    theirs = api(FixedClock(NOW), worker, them.plan.user_id)
    before = (await theirs.get("/roadmap")).json()

    pulled = await mine.post("/roadmap/pull", json={"slug": "topic-3"})
    checked = await mine.post("/progress/checkins", json={"feeling": "okay"})
    paused = await mine.post("/plan/pause", json={"days": 2})
    moved = await mine.put("/plan/study-time", json={"study_time": "07:00:00"})

    assert [r.status_code for r in (pulled, checked, paused, moved)] == [
        200,
        200,
        200,
        200,
    ]
    assert (await theirs.get("/roadmap")).json() == before
    assert [m["text"] for m in (await theirs.get("/chat/messages")).json()] == [
        "hi Sol"
    ]
