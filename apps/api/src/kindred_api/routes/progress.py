from fastapi import APIRouter, HTTPException, status

from kindred_api.dependencies import ClockDep, SessionDep
from kindred_api.plans import load_current_plan
from kindred_api.progress import check_in
from kindred_contracts import TopicRef

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("/checkins")
async def add_checkin(session: SessionDep, clock: ClockDep) -> TopicRef:
    """ "I studied today": marks the user's next topic done and returns it."""
    plan = await load_current_plan(session)
    if plan is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "there is no plan yet")
    topic = await check_in(session, plan.id, clock.now())
    if topic is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "every topic is already done")
    await session.commit()
    return topic
