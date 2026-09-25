from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from kindred_api.dependencies import (
    ClockDep,
    CurrentUserDep,
    PlanningDep,
    SessionDep,
    SourcesDep,
)
from kindred_api.onboarding import (
    AlreadyPlannedError,
    accept_plan,
    onboarding_transcript,
    onboarding_turn,
)
from kindred_api.plans import load_current_plan
from kindred_api.roadmap import build_roadmap
from kindred_contracts import (
    AcceptPlan,
    OnboardingEntry,
    OnboardingMessage,
    OnboardingReply,
    RoadmapView,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/messages")
async def list_onboarding_messages(
    session: SessionDep, clock: ClockDep, user: CurrentUserDep
) -> list[OnboardingEntry]:
    return await onboarding_transcript(session, user, clock.now())


@router.post("/messages")
async def send_onboarding_message(
    body: OnboardingMessage,
    session: SessionDep,
    clock: ClockDep,
    planning: PlanningDep,
    user: CurrentUserDep,
) -> OnboardingReply:
    """One exchange of the co-planning chat. It waits for the audited reply, since
    onboarding only shows typing dots."""
    try:
        ZoneInfo(body.timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "unknown timezone"
        ) from error
    # The phone knows where its user is; plans and rituals run in that time zone.
    user.timezone = body.timezone
    try:
        reply = await onboarding_turn(session, user, body.text, clock.now(), planning)
    except AlreadyPlannedError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    await session.commit()
    return reply


@router.post("/accept", status_code=status.HTTP_201_CREATED)
async def accept(
    body: AcceptPlan,
    session: SessionDep,
    clock: ClockDep,
    planning: PlanningDep,
    user: CurrentUserDep,
    sources: SourcesDep,
    background: BackgroundTasks,
) -> RoadmapView:
    try:
        await accept_plan(
            session, user, body.proposal_message_id, body.buddy_name, planning.courses
        )
    except AlreadyPlannedError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    except LookupError as error:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(error)) from error
    await session.commit()
    plan = await load_current_plan(session, user.id)
    assert plan is not None
    background.add_task(sources.fetch_for, plan.id, plan.curriculum_slug)
    return await build_roadmap(session, plan, clock.now())
