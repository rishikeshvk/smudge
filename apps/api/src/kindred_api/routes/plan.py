from dataclasses import replace

from fastapi import APIRouter

from kindred_api.dependencies import ClockDep, CurrentUserDep, SessionDep
from kindred_api.replan import change_study_time, pause
from kindred_api.roadmap import build_roadmap
from kindred_api.routes.roadmap import require_plan
from kindred_contracts import PausePlan, RoadmapView, StudyTimeChange

router = APIRouter(prefix="/plan", tags=["plan"])


@router.post("/pause")
async def pause_plan(
    change: PausePlan, session: SessionDep, clock: ClockDep, user: CurrentUserDep
) -> RoadmapView:
    """Move every topic still ahead back some days."""
    plan = await require_plan(session, user.id)
    await pause(session, plan, change.days, clock.now())
    await session.commit()
    return await build_roadmap(session, plan, clock.now())


@router.put("/study-time")
async def change_plan_study_time(
    change: StudyTimeChange,
    session: SessionDep,
    clock: ClockDep,
    user: CurrentUserDep,
) -> RoadmapView:
    plan = await require_plan(session, user.id)
    await change_study_time(session, plan, change.study_time, clock.now())
    await session.commit()
    return await build_roadmap(
        session, replace(plan, study_time=change.study_time), clock.now()
    )
