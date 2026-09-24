from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from kindred_api.dependencies import ClockDep, SessionDep, WorkerDep
from kindred_api.mood import STEADY, load_mood
from kindred_api.plans import load_current_plan
from kindred_api.study_window import load_studying
from kindred_contracts import BuddyStatus
from kindred_db import Buddy

router = APIRouter(tags=["buddy"])


@router.get("/buddy")
async def read_buddy(
    session: SessionDep, clock: ClockDep, worker: WorkerDep
) -> BuddyStatus:
    name = await session.scalar(select(Buddy.name).order_by(Buddy.id).limit(1))
    if name is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "there is no buddy yet")
    plan = await load_current_plan(session)
    if plan is None:
        return BuddyStatus(
            name=name, mood=STEADY, available=worker.available, studying=None
        )
    now = clock.now()
    studying = await load_studying(session, plan.id, plan.session_length, now)
    return BuddyStatus(
        name=name,
        mood=await load_mood(session, plan.id, plan.tz, studying, now),
        available=worker.available,
        studying=studying,
    )
