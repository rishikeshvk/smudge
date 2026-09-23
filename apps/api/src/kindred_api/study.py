from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.embedding import DocumentEmbedder
from kindred_api.ledger import append_note
from kindred_contracts import (
    AuditVerdict,
    EarlierNote,
    NoteDraft,
    StudyBrief,
    TopicRef,
    Verdict,
)
from kindred_db import Plan, StudySession, TopicNode
from kindred_gate import TopicMap, list_notes, load_topic_map, read_sources
from kindred_gate.jargon import jargon_in
from kindred_llm import StructuredOutputError

STUDY_ATTEMPTS = 2


class NoteWriter(Protocol):
    model: str

    async def study(self, brief: StudyBrief, session_id: str) -> NoteDraft: ...


class NoteAuditor(Protocol):
    model: str

    async def audit_note(
        self, note: str, topics: TopicMap, now: datetime, session_id: str
    ) -> AuditVerdict: ...


@dataclass(frozen=True)
class StudyComponents:
    curator: NoteWriter
    auditor: NoteAuditor
    embedder: DocumentEmbedder


class StudyStatus(StrEnum):
    WRITTEN = "written"
    # Every draft leaked or was invalid, so the buddy wrote nothing: fail closed.
    FAILED = "failed"
    # No sources ingested yet; tried again on the next tick.
    NO_SOURCES = "no_sources"


@dataclass(frozen=True)
class StudyOutcome:
    topic: TopicRef
    status: StudyStatus


async def due_topics(
    session: AsyncSession, plan_id: int, now: datetime
) -> list[TopicNode]:
    """Unlocked topics the buddy hasn't sat down to study yet, in plan order."""
    studied = exists().where(StudySession.node_id == TopicNode.id)
    nodes = await session.scalars(
        select(TopicNode)
        .where(TopicNode.plan_id == plan_id, TopicNode.unlock_at <= now, ~studied)
        .order_by(TopicNode.day)
    )
    return list(nodes)


async def study_topic(
    session: AsyncSession,
    node: TopicNode,
    now: datetime,
    components: StudyComponents,
) -> StudyOutcome:
    """One night's study: draft a note from the sources, audit it, and write it only
    if it reveals nothing locked. Commits nothing; the caller does."""
    plan = await session.get_one(Plan, node.plan_id)
    topic = TopicRef(slug=node.slug, title=node.title, day=node.day)
    sources = await read_sources(session, plan_id=plan.id, node_id=node.id, now=now)
    if not sources:
        return StudyOutcome(topic, StudyStatus.NO_SOURCES)

    topics = await load_topic_map(session, plan.id)
    earlier = [
        EarlierNote(topic=note.topic, shaky=note.shaky)
        for note in await list_notes(session, plan_id=plan.id, now=now)
        if note.topic.day < node.day
    ]
    brief = StudyBrief(
        plan_title=plan.title,
        topic=topic,
        focus=node.audit_brief,
        baseline_card=plan.baseline_card,
        earlier=earlier,
        sources=sources,
    )
    session_id = f"study-{plan.id}-{node.slug}"
    attempts: list[dict[str, object]] = []
    for _ in range(STUDY_ATTEMPTS):
        try:
            draft = await components.curator.study(brief, f"{session_id}:curator")
        except StructuredOutputError:
            break
        # Judged at the topic's own unlock, so a late study can't cover later days.
        verdict = await _audit(
            draft, topics, node.unlock_at, components.auditor, f"{session_id}:auditor"
        )
        attempts.append(
            {
                "note": draft.model_dump(mode="json"),
                "audit": verdict.model_dump(mode="json"),
            }
        )
        if verdict.verdict is Verdict.PASS:
            [vector] = await components.embedder.embed_documents(
                [f"{node.title}\n\n{draft.body}"]
            )
            note_id = await append_note(
                session,
                node_id=node.id,
                note=draft,
                written_at=now,
                embedding=vector,
                embedding_model=components.embedder.model,
            )
            session.add(
                StudySession(
                    node_id=node.id,
                    status=StudyStatus.WRITTEN.value,
                    at=now,
                    note_id=note_id,
                    attempts=attempts,
                )
            )
            return StudyOutcome(topic, StudyStatus.WRITTEN)
        brief = brief.model_copy(
            update={"feedback": _feedback(draft, verdict, topics, node.unlock_at)}
        )

    session.add(
        StudySession(
            node_id=node.id,
            status=StudyStatus.FAILED.value,
            at=now,
            note_id=None,
            attempts=attempts,
        )
    )
    return StudyOutcome(topic, StudyStatus.FAILED)


async def _audit(
    draft: NoteDraft,
    topics: TopicMap,
    at: datetime,
    auditor: NoteAuditor,
    session_id: str,
) -> AuditVerdict:
    text = _note_text(draft)
    # Locked jargon is a sure leak, so it skips the LLM call.
    jargon = jargon_in(text, topics, at)
    if jargon:
        return AuditVerdict(
            verdict=Verdict.LEAK,
            leaked_topic_slugs=list(dict.fromkeys(topic.slug for topic, _ in jargon)),
            rationale="uses locked terms: "
            + ", ".join(dict.fromkeys(word.term for _, word in jargon)),
        )
    try:
        return await auditor.audit_note(text, topics, at, session_id)
    except StructuredOutputError:
        return AuditVerdict(
            verdict=Verdict.LEAK, rationale="auditor output was invalid"
        )


def _note_text(draft: NoteDraft) -> str:
    return "\n".join([draft.body, *draft.shaky])


def _feedback(
    draft: NoteDraft, verdict: AuditVerdict, topics: TopicMap, at: datetime
) -> str:
    titles = [
        topic.title
        for slug in verdict.leaked_topic_slugs
        if (topic := topics.get(slug)) is not None
    ]
    text = _note_text(draft)
    # Only quote the draft back to itself, so the auditor can't pass locked content on.
    quotes = [e for e in verdict.evidence if e.strip() and e in text]
    lines = [
        "Your last draft went beyond today's topic into ones you haven't studied yet"
        + (f": {', '.join(titles)}." if titles else "."),
        "Rewrite it about today's topic only, leaving those parts out entirely.",
    ]
    terms = list(dict.fromkeys(word.term for _, word in jargon_in(text, topics, at)))
    if terms:
        lines.append("Don't use these terms: " + ", ".join(terms))
    if quotes:
        lines += ["Remove these parts:", *(f"- {quote}" for quote in quotes)]
    return "\n".join(lines)
