from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_contracts import RoadmapEntry, TopicRef, VocabularyKind, VocabularyTerm
from kindred_db import Plan, TopicNode, TopicVocabulary


@dataclass(frozen=True)
class Topic:
    slug: str
    day: int
    title: str
    audit_brief: str
    unlock_at: datetime
    vocabulary: list[VocabularyTerm]

    @property
    def ref(self) -> TopicRef:
        return TopicRef(slug=self.slug, title=self.title, day=self.day)

    def is_unlocked(self, now: datetime) -> bool:
        return self.unlock_at <= now


@dataclass(frozen=True)
class TopicMap:
    """Curriculum metadata for one plan. Titles are public; briefs are auditor-only."""

    plan_id: int
    baseline_card: list[str]
    topics: list[Topic]

    def get(self, slug: str) -> Topic | None:
        return next((t for t in self.topics if t.slug == slug), None)

    def unlocked(self, now: datetime) -> list[Topic]:
        return [t for t in self.topics if t.is_unlocked(now)]

    def locked(self, now: datetime) -> list[Topic]:
        return [t for t in self.topics if not t.is_unlocked(now)]

    def roadmap(self, now: datetime) -> list[RoadmapEntry]:
        return [
            RoadmapEntry(topic=t.ref, unlocked=t.is_unlocked(now)) for t in self.topics
        ]


async def load_topic_map(session: AsyncSession, plan_id: int) -> TopicMap:
    plan = await session.get_one(Plan, plan_id)
    nodes = (
        await session.scalars(
            select(TopicNode)
            .where(TopicNode.plan_id == plan_id)
            .order_by(TopicNode.day)
        )
    ).all()
    words = (
        await session.scalars(
            select(TopicVocabulary).where(
                TopicVocabulary.node_id.in_([n.id for n in nodes])
            )
        )
    ).all()
    return TopicMap(
        plan_id=plan_id,
        baseline_card=plan.baseline_card,
        topics=[
            Topic(
                slug=node.slug,
                day=node.day,
                title=node.title,
                audit_brief=node.audit_brief,
                unlock_at=node.unlock_at,
                vocabulary=[
                    VocabularyTerm(
                        term=w.term, kind=VocabularyKind(w.kind), everyday=w.everyday
                    )
                    for w in words
                    if w.node_id == node.id
                ],
            )
            for node in nodes
        ],
    )
