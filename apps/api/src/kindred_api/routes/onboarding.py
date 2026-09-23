from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from kindred_api.dependencies import ClockDep, PlanningDep, SessionDep
from kindred_api.onboarding import (
    AlreadyPlannedError,
    accept_plan,
    ensure_user,
    onboarding_turn,
)
from kindred_api.plans import load_current_plan
from kindred_api.roadmap import build_roadmap
from kindred_contracts import (
    AcceptPlan,
    OnboardingMessage,
    OnboardingReply,
    RoadmapView,
)
from kindred_db import User

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/messages")
async def send_onboarding_message(
    body: OnboardingMessage,
    session: SessionDep,
    clock: ClockDep,
    planning: PlanningDep,
) -> OnboardingReply:
    """One exchange of the co-planning chat. It waits for the audited reply, since
    onboarding only shows typing dots."""
    try:
        ZoneInfo(body.timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "unknown timezone"
        ) from error
    user = await ensure_user(session, body.timezone)
    try:
        reply = await onboarding_turn(session, user, body.text, clock.now(), planning)
    except AlreadyPlannedError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    await session.commit()
    return reply


@router.post("/accept", status_code=status.HTTP_201_CREATED)
async def accept(
    body: AcceptPlan, session: SessionDep, clock: ClockDep, planning: PlanningDep
) -> RoadmapView:
    user = await session.scalar(select(User).order_by(User.id).limit(1))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such proposal")
    try:
        await accept_plan(
            session, user, body.proposal_message_id, body.buddy_name, planning.courses
        )
    except AlreadyPlannedError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except LookupError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    await session.commit()
    plan = await load_current_plan(session)
    assert plan is not None
    return await build_roadmap(session, plan, clock.now())
