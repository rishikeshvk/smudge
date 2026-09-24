from dataclasses import dataclass
from datetime import datetime, time

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.plans import CurrentPlan
from kindred_api.schedule import plan_moment
from kindred_db import Plan, StudySession, TopicNode, TopicPrerequisite

# Only topics that are still locked and unstudied ever move, so nothing the buddy has
# written changes visibility. Topic nodes aren't the ledger, so they may be updated.


class ReplanError(Exception):
    """The change isn't possible on this plan right now."""


@dataclass(frozen=True)
class Movable:
    """The topics that can still move, in day order, with their prerequisites."""

    nodes: list[TopicNode]
    prerequisite_days: dict[int, list[int]]

    def pullable(self) -> list[TopicNode]:
        """Topics that can move into the slot: the first movable day."""
        if not self.nodes:
            return []
        slot = self.nodes[0].day
        return [
            node
            for node in self.nodes[1:]
            if all(day < slot for day in self.prerequisite_days.get(node.id, []))
        ]


async def load_movable(session: AsyncSession, plan_id: int, now: datetime) -> Movable:
    studied = exists().where(StudySession.node_id == TopicNode.id)
    nodes = list(
        await session.scalars(
            select(TopicNode)
            .where(TopicNode.plan_id == plan_id, TopicNode.unlock_at > now, ~studied)
            .order_by(TopicNode.day)
        )
    )
    rows = await session.execute(
        select(TopicPrerequisite.node_id, TopicNode.day)
        .join(TopicNode, TopicPrerequisite.prerequisite_id == TopicNode.id)
        .where(TopicPrerequisite.node_id.in_([node.id for node in nodes]))
    )
    prerequisite_days: dict[int, list[int]] = {}
    for node_id, day in rows.tuples():
        prerequisite_days.setdefault(node_id, []).append(day)
    return Movable(nodes, prerequisite_days)


async def pull_earlier(
    session: AsyncSession, plan: CurrentPlan, slug: str, now: datetime
) -> None:
    """Move a topic into the next free study slot; the topics from that slot up to
    its old day each move back one day, so the plan still ends on the same day."""
    movable = await load_movable(session, plan.id, now)
    pulled = next((n for n in movable.pullable() if n.slug == slug), None)
    if pulled is None:
        raise ReplanError(f"{slug} can't be pulled earlier")
    slot = movable.nodes[0].day
    for node in movable.nodes:
        if slot <= node.day < pulled.day:
            _move(node, node.day + 1, plan, plan.study_time)
    _move(pulled, slot, plan, plan.study_time)
    await session.flush()


async def pause(
    session: AsyncSession, plan: CurrentPlan, days: int, now: datetime
) -> None:
    """Every topic still ahead moves back some days."""
    for node in (await load_movable(session, plan.id, now)).nodes:
        _move(node, node.day + days, plan, plan.study_time)
    await session.flush()


async def change_study_time(
    session: AsyncSession, plan: CurrentPlan, study_time: time, now: datetime
) -> None:
    """A new daily study time, for the topics still ahead."""
    row = await session.get_one(Plan, plan.id)
    row.study_time = study_time
    for node in (await load_movable(session, plan.id, now)).nodes:
        _move(node, node.day, plan, study_time)
    await session.flush()


def _move(node: TopicNode, day: int, plan: CurrentPlan, study_time: time) -> None:
    node.day = day
    node.unlock_at = plan_moment(plan.start_date, day, study_time, plan.tz)
