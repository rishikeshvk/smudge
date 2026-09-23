from dataclasses import dataclass
from datetime import date, time
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.schedule import plan_moment
from kindred_contracts import Curriculum
from kindred_db import Plan, TopicNode, TopicPrerequisite, TopicVocabulary, User


@dataclass(frozen=True)
class CurrentPlan:
    id: int
    user_id: int
    curriculum_slug: str
    title: str
    start_date: date
    study_time: time
    tz: ZoneInfo


async def load_current_plan(session: AsyncSession) -> CurrentPlan | None:
    """The one plan the single hardcoded user has, if onboarding has made it."""
    row = (
        await session.execute(
            select(Plan, User.timezone)
            .join(User, Plan.user_id == User.id)
            .order_by(Plan.id)
            .limit(1)
        )
    ).first()
    if row is None:
        return None
    plan, timezone = row
    return CurrentPlan(
        id=plan.id,
        user_id=plan.user_id,
        curriculum_slug=plan.curriculum_slug,
        title=plan.title,
        start_date=plan.start_date,
        study_time=plan.study_time,
        tz=ZoneInfo(timezone),
    )


async def create_plan(
    session: AsyncSession,
    user_id: int,
    curriculum: Curriculum,
    start_date: date,
    study_time: time,
    tz: ZoneInfo,
) -> Plan:
    """A plan and its topic graph; each topic unlocks at the study time on its day."""
    plan = Plan(
        user_id=user_id,
        curriculum_slug=curriculum.slug,
        title=curriculum.title,
        start_date=start_date,
        study_time=study_time,
        baseline_card=curriculum.baseline_card,
    )
    session.add(plan)
    await session.flush()

    nodes = {
        topic.slug: TopicNode(
            plan_id=plan.id,
            slug=topic.slug,
            day=topic.day,
            title=topic.title,
            audit_brief=topic.audit_brief,
            unlock_at=plan_moment(start_date, topic.day, study_time, tz),
        )
        for topic in curriculum.nodes
    }
    session.add_all(nodes.values())
    await session.flush()
    for topic in curriculum.nodes:
        node = nodes[topic.slug]
        session.add_all(
            TopicPrerequisite(node_id=node.id, prerequisite_id=nodes[slug].id)
            for slug in topic.prerequisites
        )
        session.add_all(
            TopicVocabulary(
                node_id=node.id,
                term=word.term,
                kind=word.kind.value,
                everyday=word.everyday,
            )
            for word in topic.vocabulary
        )
    await session.flush()
    return plan
