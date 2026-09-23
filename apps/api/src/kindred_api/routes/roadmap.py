from fastapi import APIRouter, HTTPException, status

from kindred_api.dependencies import ClockDep, SessionDep
from kindred_api.plans import load_current_plan
from kindred_api.progress import studied_slugs
from kindred_api.schedule import plan_day
from kindred_contracts import RoadmapTopic, RoadmapView
from kindred_gate import list_notes, load_topic_map

router = APIRouter(tags=["roadmap"])


@router.get("/roadmap")
async def read_roadmap(session: SessionDep, clock: ClockDep) -> RoadmapView:
    """The shared plan: every title is public, since the user co-created it."""
    plan = await load_current_plan(session)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "there is no plan yet")
    now = clock.now()
    topics = await load_topic_map(session, plan.id)
    written = {
        note.topic.slug for note in await list_notes(session, plan_id=plan.id, now=now)
    }
    studied = await studied_slugs(session, plan.id, now)
    return RoadmapView(
        plan_title=plan.title,
        day=plan_day(plan.start_date, now, plan.tz),
        topics=[
            RoadmapTopic(
                topic=topic.ref,
                unlocks_at=topic.unlock_at,
                unlocked=topic.is_unlocked(now),
                buddy_studied=topic.slug in written,
                user_studied=topic.slug in studied,
            )
            for topic in topics.topics
        ],
    )
