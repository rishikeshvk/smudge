from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.catalog import all_locked, as_course
from kindred_api.chat import HISTORY_LIMIT, Thread, read_thread, to_contract
from kindred_api.plans import create_plan, load_current_plan
from kindred_contracts import (
    AuditVerdict,
    ChatTurn,
    Curriculum,
    OnboardingEntry,
    OnboardingReply,
    PlanChoice,
    PlannerBrief,
    PlannerDraft,
    PlanProposal,
    Speaker,
    TopicRef,
    Verdict,
)
from kindred_db import Buddy, Message, Plan, User
from kindred_gate import Auditor
from kindred_llm import StructuredOutputError

PLANNER_ATTEMPTS = 2
# Onboarding is a short conversation; this only bounds a runaway one.
TRANSCRIPT_LIMIT = 200
# Sent when every draft failed its audit, so it may never name any topic's content.
FALLBACK = (
    "let's save the details for when we actually get there! "
    "so, what would you like to learn, and by when?"
)


class AlreadyPlannedError(Exception):
    pass


class PlanDrafter(Protocol):
    model: str

    async def plan(self, brief: PlannerBrief, session_id: str) -> PlannerDraft: ...


@dataclass(frozen=True)
class Planning:
    courses: list[Curriculum]
    planner: PlanDrafter
    auditor: Auditor


async def onboarding_transcript(
    session: AsyncSession, user: User, now: datetime
) -> list[OnboardingEntry]:
    """The onboarding chat so far, so the app can pick it up after a restart."""
    messages = await read_thread(
        session,
        user.id,
        now,
        thread=Thread.ONBOARDING,
        before_id=None,
        limit=TRANSCRIPT_LIMIT,
    )
    return [
        OnboardingEntry(
            message=to_contract(message),
            proposal=PlanProposal.model_validate(message.proposal)
            if message.proposal is not None
            else None,
        )
        for message in messages
    ]


async def onboarding_turn(
    session: AsyncSession, user: User, text: str, now: datetime, planning: Planning
) -> OnboardingReply:
    """One exchange of the co-planning chat. Every reply is audited with every topic
    locked, because the buddy hasn't studied anything yet."""
    if await load_current_plan(session, user.id) is not None:
        raise AlreadyPlannedError("there is already a plan")
    earlier = await read_thread(
        session,
        user.id,
        now,
        thread=Thread.ONBOARDING,
        before_id=None,
        limit=HISTORY_LIMIT,
    )
    history = [ChatTurn(speaker=Speaker(m.speaker), text=m.text) for m in earlier]
    today = now.astimezone(ZoneInfo(user.timezone)).date()
    brief = PlannerBrief(
        today=today,
        courses=[as_course(course) for course in planning.courses],
        conversation=history,
        message=text,
    )
    topics = all_locked(planning.courses, now)
    session_id = f"onboarding-{user.id}"

    passed: PlannerDraft | None = None
    choice: PlanChoice | None = None
    for _ in range(PLANNER_ATTEMPTS):
        try:
            draft = await planning.planner.plan(brief, f"{session_id}:planner")
        except StructuredOutputError:
            break
        choice = draft.plan or choice
        spoken = "\n".join([draft.reply, *draft.quick_replies])
        try:
            verdict = await planning.auditor.audit(
                spoken, text, history, topics, now, f"{session_id}:auditor"
            )
        except StructuredOutputError:
            verdict = AuditVerdict(verdict=Verdict.LEAK, rationale="invalid audit")
        if verdict.verdict is Verdict.PASS:
            passed = draft
            break
        brief = brief.model_copy(update={"feedback": _feedback(spoken, verdict)})

    # The card is built by code from public titles, so it survives a failed draft.
    proposal = _proposal(choice, planning.courses, today) if choice else None
    asked = Message(
        user_id=user.id,
        thread=Thread.ONBOARDING.value,
        speaker=Speaker.USER.value,
        text=text,
        at=now,
    )
    session.add(asked)
    await session.flush()
    reply = Message(
        user_id=user.id,
        thread=Thread.ONBOARDING.value,
        speaker=Speaker.BUDDY.value,
        text=passed.reply if passed else FALLBACK,
        at=now,
        reply_to_id=asked.id,
        proposal=proposal.model_dump(mode="json") if proposal else None,
    )
    session.add(reply)
    await session.flush()
    return OnboardingReply(
        message=to_contract(reply),
        quick_replies=passed.quick_replies if passed else [],
        proposal=proposal,
    )


async def accept_plan(
    session: AsyncSession,
    user: User,
    proposal_message_id: int,
    buddy_name: str,
    courses: list[Curriculum],
) -> Plan:
    """Turn an accepted proposal into the plan, and name the buddy for good."""
    if await load_current_plan(session, user.id) is not None:
        raise AlreadyPlannedError("there is already a plan")
    message = await session.get(Message, proposal_message_id)
    if message is None or message.user_id != user.id or message.proposal is None:
        raise LookupError("no such proposal")
    proposal = PlanProposal.model_validate(message.proposal)
    curriculum = next(c for c in courses if c.slug == proposal.curriculum_slug)
    plan = await create_plan(
        session,
        user.id,
        curriculum,
        proposal.start_date,
        proposal.study_time,
        round(proposal.hours_per_day * 60),
        ZoneInfo(user.timezone),
    )
    buddy = await session.scalar(select(Buddy).where(Buddy.user_id == user.id))
    if buddy is None:
        session.add(Buddy(user_id=user.id, name=buddy_name))
    else:
        buddy.name = buddy_name
    await session.flush()
    return plan


def _proposal(
    choice: PlanChoice, courses: list[Curriculum], today: date
) -> PlanProposal | None:
    course = next((c for c in courses if c.slug == choice.curriculum_slug), None)
    # An invented course or a start in the past is no plan at all.
    if course is None or choice.start_date < today:
        return None
    return PlanProposal(
        curriculum_slug=course.slug,
        title=course.title,
        start_date=choice.start_date,
        study_time=choice.study_time,
        hours_per_day=choice.hours_per_day,
        topics=[
            TopicRef(slug=node.slug, title=node.title, day=node.day)
            for node in course.nodes
        ],
    )


def _feedback(spoken: str, verdict: AuditVerdict) -> str:
    quotes = [e for e in verdict.evidence if e.strip() and e in spoken]
    lines = [
        "Your last draft explained or previewed what a topic covers, but you haven't "
        "studied anything yet. Rewrite it using topic titles only.",
    ]
    if quotes:
        lines += ["Remove these parts:", *(f"- {quote}" for quote in quotes)]
    return "\n".join(lines)
