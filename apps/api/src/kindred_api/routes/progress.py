from fastapi import APIRouter, HTTPException, status

from kindred_api.chat import post_message
from kindred_api.dependencies import ClockDep, SessionDep, WorkerDep
from kindred_api.plans import load_current_plan
from kindred_api.progress import check_in, checkin_text
from kindred_contracts import CheckIn, CheckinCard, TopicRef

router = APIRouter(prefix="/progress", tags=["progress"])


@router.post("/checkins")
async def add_checkin(
    body: CheckIn, session: SessionDep, clock: ClockDep, worker: WorkerDep
) -> TopicRef:
    """ "I studied today": marks the user's next topic done, and tells the buddy how it
    went so it can compare notes."""
    plan = await load_current_plan(session)
    if plan is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "there is no plan yet")
    now = clock.now()
    topic = await check_in(session, plan.id, now, body.feeling, body.fuzzy)
    if topic is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "every topic is already done")
    card = CheckinCard(
        kind="checkin", topic=topic, feeling=body.feeling, fuzzy=body.fuzzy
    )
    await post_message(session, plan.user_id, checkin_text(topic, body), now, card)
    await session.commit()
    worker.wake()
    return topic
