from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.plans import CurrentPlan, load_current_plan
from kindred_api.reflection import (
    ReflectionComponents,
    reflect_day,
    unreflected_days,
)
from kindred_api.turn_log import record_turn
from kindred_contracts import (
    AuditVerdict,
    Category,
    Classification,
    Directive,
    ReflectedPoint,
    Reflection,
    ReflectionBrief,
    RoleModels,
    Route,
    TopicRef,
    TurnTrace,
    Verdict,
)
from kindred_db import Plan, SourceDocument, TopicNode
from kindred_gate import TopicMap, list_notes
from kindred_llm import StructuredOutputError

AddCourse = Callable[[int], Awaitable[Plan]]
AddStudy = Callable[..., Awaitable[None]]
# 20:30 on day 1 in Kolkata, then 09:00 the next morning.
EVENING = datetime(2026, 10, 1, 15, 0, tzinfo=UTC)
NEXT_MORNING = datetime(2026, 10, 2, 3, 30, tzinfo=UTC)
TOPIC_1 = TopicRef(slug="topic-1", title="Topic 1", day=1)
PASS = AuditVerdict(verdict=Verdict.PASS, rationale="fine")
LEAK = AuditVerdict(verdict=Verdict.LEAK, rationale="locked")


class FakeReflector:
    model = "fake-reflector"

    def __init__(self, result: Reflection | Exception) -> None:
        self._result = result
        self.briefs: list[ReflectionBrief] = []

    async def reflect(self, brief: ReflectionBrief, session_id: str) -> Reflection:
        self.briefs.append(brief)
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


class FakeAuditor:
    model = "fake-auditor"

    def __init__(self, verdict: AuditVerdict) -> None:
        self._verdict = verdict

    async def audit_note(
        self, note: str, topics: TopicMap, now: datetime, session_id: str
    ) -> AuditVerdict:
        return self._verdict


def sorted_point(
    shaky: str, insight: str = "regions keep failures apart"
) -> Reflection:
    return Reflection(
        points=[ReflectedPoint(shaky=shaky, sorted=True, insight=insight)]
    )


async def explained(
    session: AsyncSession, add_course: AddCourse, add_study: AddStudy
) -> CurrentPlan:
    """Day 1 studied with two shaky points, sourced, and the user explaining one."""
    course = await add_course(2)
    await add_study(
        1, EVENING - timedelta(hours=1), shaky=["why regions?", "what's an AZ?"]
    )
    node_id = await session.scalar(select(TopicNode.id).where(TopicNode.day == 1))
    assert node_id is not None
    session.add(
        SourceDocument(
            node_id=node_id,
            url="https://docs.test/regions",
            title="Regions",
            text="Regions are isolated so a failure stays in one.",
            fetched_at=EVENING,
        )
    )
    plan = await load_current_plan(session, course.user_id)
    assert plan is not None
    await record_turn(
        session,
        TurnTrace(
            message="regions exist so one failing doesn't take the rest down",
            at=EVENING,
            classification=Classification(
                category=Category.CURRICULUM, topic_slugs=["topic-1"], rationale=""
            ),
            directive=Directive(route=Route.ANSWER, answer_topics=[TOPIC_1]),
            retrieved=[],
            attempts=[],
            final_reply="oh, that makes sense",
            fell_back=False,
            models=RoleModels(classifier="c", drafter="d", auditor="a"),
            latency_ms=1,
        ),
        plan_id=plan.id,
        session_id="chat-1",
    )
    return plan


@pytest.mark.anyio
async def test_an_explained_point_is_sorted_once_the_day_is_over(
    session: AsyncSession, add_course: AddCourse, add_study: AddStudy
) -> None:
    plan = await explained(session, add_course, add_study)
    reflector = FakeReflector(sorted_point("why regions?"))

    assert await unreflected_days(session, plan, EVENING) == []
    assert await unreflected_days(session, plan, NEXT_MORNING) == [date(2026, 10, 1)]

    written = await reflect_day(
        session,
        plan,
        date(2026, 10, 1),
        NEXT_MORNING,
        ReflectionComponents(reflector=reflector, auditor=FakeAuditor(PASS)),
    )

    assert written == 1
    [brief] = reflector.briefs
    assert brief.open_shaky == ["why regions?", "what's an AZ?"]
    assert brief.exchanges[0].text.startswith("regions exist")
    [note] = await list_notes(session, plan_id=plan.id, now=NEXT_MORNING)
    assert [(p.shaky, p.insight) for p in note.sorted] == [
        ("why regions?", "regions keep failures apart")
    ]
    assert await unreflected_days(session, plan, NEXT_MORNING) == []


@pytest.mark.anyio
async def test_nothing_is_sorted_without_a_passing_audit(
    session: AsyncSession, add_course: AddCourse, add_study: AddStudy
) -> None:
    plan = await explained(session, add_course, add_study)

    written = await reflect_day(
        session,
        plan,
        date(2026, 10, 1),
        NEXT_MORNING,
        ReflectionComponents(
            reflector=FakeReflector(sorted_point("why regions?")),
            auditor=FakeAuditor(LEAK),
        ),
    )

    assert written == 0


@pytest.mark.anyio
@pytest.mark.parametrize(
    "result",
    [
        # A point the note never had, and one the model didn't mark sorted.
        sorted_point("something made up"),
        Reflection(points=[ReflectedPoint(shaky="why regions?", sorted=False)]),
        StructuredOutputError("bad json"),
    ],
)
async def test_only_real_sorted_points_count(
    session: AsyncSession,
    add_course: AddCourse,
    add_study: AddStudy,
    result: Reflection | Exception,
) -> None:
    plan = await explained(session, add_course, add_study)

    written = await reflect_day(
        session,
        plan,
        date(2026, 10, 1),
        NEXT_MORNING,
        ReflectionComponents(
            reflector=FakeReflector(result), auditor=FakeAuditor(PASS)
        ),
    )

    assert written == 0
    assert await unreflected_days(session, plan, NEXT_MORNING) == []
