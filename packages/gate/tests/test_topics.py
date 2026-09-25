from datetime import UTC, date, datetime, time, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_contracts import VocabularyKind
from kindred_db import Plan, TopicNode, TopicVocabulary, User
from kindred_gate import load_topic_map

UNLOCK = datetime(2026, 10, 1, 13, 30, tzinfo=UTC)


@pytest.mark.anyio
async def test_topic_map_holds_plan_topics_in_day_order(session: AsyncSession) -> None:
    user = User(timezone="UTC")
    session.add(user)
    await session.flush()
    plan = Plan(
        user_id=user.id,
        curriculum_slug="t",
        title="T",
        start_date=date(2026, 10, 1),
        study_time=time(19),
        baseline_card=["AWS is Amazon's cloud."],
    )
    session.add(plan)
    await session.flush()
    later = TopicNode(
        plan_id=plan.id,
        slug="later",
        day=2,
        title="Later",
        audit_brief="Later brief",
        unlock_at=UNLOCK + timedelta(days=1),
    )
    first = TopicNode(
        plan_id=plan.id,
        slug="first",
        day=1,
        title="First",
        audit_brief="First brief",
        unlock_at=UNLOCK,
    )
    session.add_all([later, first])
    await session.flush()
    session.add(
        TopicVocabulary(
            node_id=first.id, term="IAM", kind="abbreviation", everyday=False
        )
    )
    await session.flush()

    topics = await load_topic_map(session, plan.id)

    assert topics.baseline_card == ["AWS is Amazon's cloud."]
    assert [t.slug for t in topics.topics] == ["first", "later"]
    assert topics.topics[0].vocabulary[0].kind is VocabularyKind.ABBREVIATION
    assert [t.slug for t in topics.unlocked(UNLOCK)] == ["first"]
    assert [
        (e.unlocked, e.has_note) for e in topics.roadmap(UNLOCK, frozenset(["first"]))
    ] == [(True, True), (False, False)]
