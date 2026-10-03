from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.demo import DemoUnavailableError, ask_demo, demo_turn
from kindred_api.dependencies import DemoBudgetDep, LLMRuntimeDep, SessionDep
from kindred_api.plans import CurrentPlan, load_demo_plan
from kindred_contracts import AskDemo, DemoInfo, DemoTurn
from kindred_db import Buddy
from kindred_gate import load_topic_map
from kindred_llm import LLMUnavailableError

# No user here: strangers only reach the demo buddy, found by its flag (invariant 8).
router = APIRouter(prefix="/demo", tags=["demo"])


async def _plan(session: AsyncSession) -> CurrentPlan:
    plan = await load_demo_plan(session)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return plan


@router.get("")
async def read_demo(session: SessionDep, budget: DemoBudgetDep) -> DemoInfo:
    """The demo buddy and its plan's days, for the landing page."""
    plan = await _plan(session)
    topics = await load_topic_map(session, plan.id)
    name = await session.scalar(select(Buddy.name).where(Buddy.user_id == plan.user_id))
    return DemoInfo(
        buddy_name=name or "",
        days=[topic.ref for topic in topics.topics],
        turns_left=budget.turns_left(),
    )


@router.post("/turns")
async def ask(
    body: AskDemo,
    request: Request,
    session: SessionDep,
    budget: DemoBudgetDep,
    llm: LLMRuntimeDep,
) -> DemoTurn:
    """One audited reply from the demo buddy, on the plan day the visitor picked."""
    plan = await _plan(session)
    topics = await load_topic_map(session, plan.id)
    if body.day > len(topics.topics):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "no such day")
    try:
        async with budget.spend(_client(request)):
            trace = await ask_demo(session, plan, topics, body, llm.turn_components)
    except DemoUnavailableError as error:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(error)) from error
    except LLMUnavailableError as error:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "The buddy is unavailable right now."
        ) from error
    await session.commit()
    return demo_turn(trace, topics, budget.turns_left())


def _client(request: Request) -> str | None:
    # A proxy appends the address it saw, so the last entry is the one to trust.
    # Without the header every caller looks local, so only the daily cap applies.
    forwarded = request.headers.get("X-Forwarded-For")
    return forwarded.rsplit(",", 1)[-1].strip() if forwarded else None
