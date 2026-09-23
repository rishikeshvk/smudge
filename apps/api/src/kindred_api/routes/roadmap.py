from fastapi import APIRouter, HTTPException, status

from kindred_api.dependencies import ClockDep, SessionDep
from kindred_api.plans import load_current_plan
from kindred_api.roadmap import build_roadmap
from kindred_contracts import RoadmapView

router = APIRouter(tags=["roadmap"])


@router.get("/roadmap")
async def read_roadmap(session: SessionDep, clock: ClockDep) -> RoadmapView:
    plan = await load_current_plan(session)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "there is no plan yet")
    return await build_roadmap(session, plan, clock.now())
