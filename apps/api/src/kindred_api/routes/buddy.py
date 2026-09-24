from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from kindred_api.dependencies import ClockDep, SessionDep, TickerDep, WorkerDep
from kindred_api.mood import STEADY, load_mood
from kindred_api.plans import load_current_plan
from kindred_contracts import BuddyStatus
from kindred_db import Buddy

router = APIRouter(tags=["buddy"])


@router.get("/buddy")
async def read_buddy(
    session: SessionDep, clock: ClockDep, worker: WorkerDep, ticker: TickerDep
) -> BuddyStatus:
    name = await session.scalar(select(Buddy.name).order_by(Buddy.id).limit(1))
    if name is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "there is no buddy yet")
    plan = await load_current_plan(session)
    mood = (
        STEADY
        if plan is None
        else await load_mood(session, plan.id, plan.tz, clock.now())
    )
    return BuddyStatus(
        name=name, mood=mood, available=worker.available, studying=ticker.studying
    )
