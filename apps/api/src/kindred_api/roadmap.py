from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.plans import CurrentPlan
from kindred_api.progress import studied_slugs
from kindred_api.replan import load_movable
from kindred_api.schedule import plan_day
from kindred_api.standing import load_standing
from kindred_contracts import RoadmapTopic, RoadmapView
from kindred_gate import list_notes, load_topic_map


async def build_roadmap(
    session: AsyncSession, plan: CurrentPlan, now: datetime
) -> RoadmapView:
    """The shared plan: every title is public, since the user co-created it."""
    topics = await load_topic_map(session, plan.id)
    notes = await list_notes(session, plan_id=plan.id, now=now)
    written = {note.topic.slug for note in notes}
    studied = await studied_slugs(session, plan.id, now)
    standing = await load_standing(session, plan.id, plan.tz, now)
    pullable = {n.slug for n in (await load_movable(session, plan.id, now)).pullable()}
    return RoadmapView(
        plan_title=plan.title,
        day=plan_day(plan.start_date, now, plan.tz),
        study_time=plan.study_time,
        streak=standing.streak,
        gap=standing.gap,
        topics=[
            RoadmapTopic(
                topic=topic.ref,
                unlocks_at=topic.unlock_at,
                unlocked=topic.is_unlocked(now),
                buddy_studied=topic.slug in written,
                user_studied=topic.slug in studied,
                can_pull=topic.slug in pullable,
            )
            for topic in topics.topics
        ],
    )
