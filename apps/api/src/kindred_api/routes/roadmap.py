from fastapi import APIRouter, HTTPException, status

from kindred_api.dependencies import ClockDep, CurrentUserDep, SessionDep
from kindred_api.plans import CurrentPlan, load_current_plan
from kindred_api.replan import ReplanError, pull_earlier
from kindred_api.roadmap import build_roadmap
from kindred_contracts import PullTopic, RoadmapView

router = APIRouter(tags=["roadmap"])


@router.get("/roadmap")
async def read_roadmap(
    session: SessionDep, clock: ClockDep, user: CurrentUserDep
) -> RoadmapView:
    plan = await require_plan(session, user.id)
    return await build_roadmap(session, plan, clock.now())


@router.post("/roadmap/pull")
async def pull_topic(
    pull: PullTopic, session: SessionDep, clock: ClockDep, user: CurrentUserDep
) -> RoadmapView:
    """Pull a locked topic into the next free study slot."""
    plan = await require_plan(session, user.id)
    try:
        await pull_earlier(session, plan, pull.slug, clock.now())
    except ReplanError as error:
        raise HTTPException(status.HTTP_409_CONFLICT, str(error)) from error
    await session.commit()
    return await build_roadmap(session, plan, clock.now())


async def require_plan(session: SessionDep, user_id: int) -> CurrentPlan:
    plan = await load_current_plan(session, user_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "there is no plan yet")
    return plan
