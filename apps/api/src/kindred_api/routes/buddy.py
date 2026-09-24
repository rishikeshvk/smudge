from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from kindred_api.chat import to_contract
from kindred_api.dependencies import ClockDep, SessionDep, WorkerDep
from kindred_api.mood import STEADY, load_mood
from kindred_api.plans import load_current_plan
from kindred_api.study_together import join_session
from kindred_api.study_window import load_studying
from kindred_contracts import BuddyStatus, ChatMessage
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


@router.post("/buddy/study-together", status_code=status.HTTP_201_CREATED)
async def study_together(session: SessionDep, clock: ClockDep) -> ChatMessage:
    """Join the buddy's study session in progress."""
    plan = await load_current_plan(session)
    if plan is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "there is no plan yet")
    now = clock.now()
    studying = await load_studying(session, plan.id, plan.session_length, now)
    if studying is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "the buddy isn't studying now")
    message = await join_session(session, plan.user_id, studying, now)
    await session.commit()
    return to_contract(message)
