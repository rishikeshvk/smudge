from datetime import UTC, date, datetime, time
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.catalog import all_locked, load_catalog
from kindred_api.chat import Thread, read_thread
from kindred_api.onboarding import (
    FALLBACK,
    AlreadyPlannedError,
    Planning,
    accept_plan,
    onboarding_turn,
)
from kindred_api.plans import load_current_plan
from kindred_contracts import (
    AuditVerdict,
    ChatTurn,
    Curriculum,
    PlanChoice,
    PlannerBrief,
    PlannerDraft,
    Verdict,
)
from kindred_db import Buddy, TopicNode, User
from kindred_gate import TopicMap
from kindred_gate.jargon import jargon_in

CURRICULA = Path(__file__).parents[3] / "curricula"
# 14:30 on Wed 23 Sep in Kolkata.
NOW = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)
PASS = AuditVerdict(verdict=Verdict.PASS, rationale="fine")
LEAK = AuditVerdict(
    verdict=Verdict.LEAK, evidence=["S3 stores objects."], rationale="explains S3"
)

TINY = Curriculum.model_validate(
    {
        "slug": "tiny",
        "title": "Tiny course",
        "study_time": "19:00",
        "baseline_card": ["Clouds rent computers."],
        "nodes": [
            {
                "slug": f"topic-{day}",
                "day": day,
                "title": f"Topic {day}",
                "audit_brief": "Brief.",
                "vocabulary": [{"term": f"term{day}", "kind": "term"}],
                "notes": [{"body": "n", "shaky": ["s"], "sources": ["https://d.t"]}],
            }
            for day in (1, 2)
        ],
    }
)


def plan(start: date = date(2026, 9, 24), slug: str = "tiny") -> PlanChoice:
    return PlanChoice(
        curriculum_slug=slug, start_date=start, study_time=time(20), hours_per_day=1
    )


class FakePlanner:
    model = "fake-planner"

    def __init__(self, *drafts: PlannerDraft) -> None:
        self._drafts = list(drafts)
        self.briefs: list[PlannerBrief] = []

    async def plan(self, brief: PlannerBrief, session_id: str) -> PlannerDraft:
        self.briefs.append(brief)
        return self._drafts.pop(0)


class FakeAuditor:
    model = "fake-auditor"

    def __init__(self, *verdicts: AuditVerdict) -> None:
        self._verdicts = list(verdicts)
        self.audited: list[str] = []

    async def audit(
        self,
        draft: str,
        message: str,
        history: list[ChatTurn],
        topics: TopicMap,
        now: datetime,
        session_id: str,
    ) -> AuditVerdict:
        assert topics.unlocked(now) == []
        self.audited.append(draft)
        return self._verdicts.pop(0)


async def add_user(session: AsyncSession) -> User:
    user = User(timezone="Asia/Kolkata")
    session.add(user)
    await session.flush()
    return user


def planning(planner: FakePlanner, auditor: FakeAuditor) -> Planning:
    return Planning(courses=[TINY], planner=planner, auditor=auditor)


@pytest.mark.anyio
async def test_an_audited_reply_comes_with_its_quick_replies_and_card(
    session: AsyncSession,
) -> None:
    user = await add_user(session)
    draft = PlannerDraft(reply="an hour works", quick_replies=["ok"], plan=plan())
    auditor = FakeAuditor(PASS)

    reply = await onboarding_turn(
        session, user, "tiny, 1h", NOW, planning(FakePlanner(draft), auditor)
    )

    assert (reply.message.text, reply.quick_replies) == ("an hour works", ["ok"])
    assert reply.proposal is not None
    assert (reply.proposal.title, reply.proposal.study_time) == (
        "Tiny course",
        time(20),
    )
    assert [t.title for t in reply.proposal.topics] == ["Topic 1", "Topic 2"]
    assert auditor.audited == ["an hour works\nok"]


@pytest.mark.anyio
async def test_the_planner_sees_the_onboarding_so_far(session: AsyncSession) -> None:
    user = await add_user(session)
    planner = FakePlanner(
        PlannerDraft(reply="what's the goal?"), PlannerDraft(reply="nice")
    )
    both = planning(planner, FakeAuditor(PASS, PASS))

    await onboarding_turn(session, user, "hi", NOW, both)
    await onboarding_turn(session, user, "learn tiny", NOW, both)

    second = planner.briefs[1]
    assert [t.text for t in second.conversation] == ["hi", "what's the goal?"]
    assert second.today == date(2026, 9, 23)
    chat = await read_thread(
        session, user.id, NOW, thread=Thread.CHAT, before_id=None, limit=10
    )
    assert chat == []


@pytest.mark.anyio
async def test_a_leaky_reply_is_redrafted_then_replaced_but_keeps_its_card(
    session: AsyncSession,
) -> None:
    user = await add_user(session)
    leaky = PlannerDraft(reply="S3 stores objects.", quick_replies=["go"], plan=plan())
    planner = FakePlanner(leaky, leaky)

    reply = await onboarding_turn(
        session, user, "tiny", NOW, planning(planner, FakeAuditor(LEAK, LEAK))
    )

    assert reply.message.text == FALLBACK
    assert reply.quick_replies == []
    assert reply.proposal is not None
    feedback = planner.briefs[1].feedback
    assert feedback is not None and "- S3 stores objects." in feedback


@pytest.mark.anyio
async def test_an_invented_course_or_a_past_start_is_no_card(
    session: AsyncSession,
) -> None:
    user = await add_user(session)
    drafts = [
        PlannerDraft(reply="ok", plan=plan(slug="made-up")),
        PlannerDraft(reply="ok", plan=plan(start=date(2026, 9, 20))),
    ]
    for draft in drafts:
        reply = await onboarding_turn(
            session, user, "x", NOW, planning(FakePlanner(draft), FakeAuditor(PASS))
        )
        assert reply.proposal is None


@pytest.mark.anyio
async def test_accepting_a_card_creates_the_plan_and_names_the_buddy(
    session: AsyncSession,
) -> None:
    user = await add_user(session)
    draft = PlannerDraft(reply="ready?", plan=plan())
    reply = await onboarding_turn(
        session, user, "go", NOW, planning(FakePlanner(draft), FakeAuditor(PASS))
    )

    await accept_plan(session, user, reply.message.id, "Wren", [TINY])

    current = await load_current_plan(session, user.id)
    assert current is not None
    assert (current.start_date, current.study_time) == (date(2026, 9, 24), time(20))
    first = await session.scalar(select(TopicNode).where(TopicNode.day == 1))
    # 20:00 in Kolkata on 24 Sep.
    assert first is not None
    assert first.unlock_at == datetime(2026, 9, 24, 14, 30, tzinfo=UTC)
    assert await session.scalar(select(Buddy.name)) == "Wren"
    with pytest.raises(AlreadyPlannedError):
        await accept_plan(session, user, reply.message.id, "Wren", [TINY])


@pytest.mark.anyio
async def test_only_a_real_proposal_can_be_accepted(session: AsyncSession) -> None:
    user = await add_user(session)
    reply = await onboarding_turn(
        session,
        user,
        "hi",
        NOW,
        planning(FakePlanner(PlannerDraft(reply="hey")), FakeAuditor(PASS)),
    )

    with pytest.raises(LookupError):
        await accept_plan(session, user, reply.message.id, "Wren", [TINY])


def test_the_fallback_names_nothing_from_any_course() -> None:
    topics = all_locked(load_catalog(CURRICULA), NOW)

    assert jargon_in(FALLBACK, topics, NOW) == []
    assert "{" not in FALLBACK
