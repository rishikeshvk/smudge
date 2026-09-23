import time
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from kindred_contracts import (
    AuditVerdict,
    Category,
    ChatTurn,
    Classification,
    Draft,
    DraftAttempt,
    DraftRequest,
    RetrievedNote,
    RoleModels,
    Route,
    TurnTrace,
    Verdict,
)
from kindred_gate.fallback import fallback_reply
from kindred_gate.retrieval import retrieve_notes
from kindred_gate.routing import route
from kindred_gate.topics import TopicMap
from kindred_llm import Embedder, StructuredOutputError

NOTES_PER_TURN = 4


class Classifier(Protocol):
    model: str

    async def classify(
        self, message: str, history: list[ChatTurn], topics: TopicMap, session_id: str
    ) -> Classification: ...


class Retriever(Protocol):
    async def retrieve(self, message: str, now: datetime) -> list[RetrievedNote]: ...


class Drafter(Protocol):
    model: str

    async def draft(self, request: DraftRequest, session_id: str) -> Draft: ...


class Auditor(Protocol):
    model: str

    async def audit(
        self,
        draft: str,
        message: str,
        history: list[ChatTurn],
        topics: TopicMap,
        now: datetime,
        session_id: str,
    ) -> AuditVerdict: ...


@dataclass(frozen=True)
class TurnComponents:
    classifier: Classifier
    retriever: Retriever
    drafter: Drafter
    auditor: Auditor


class GatedRetriever:
    def __init__(self, session: AsyncSession, embedder: Embedder, plan_id: int) -> None:
        self._session = session
        self._embedder = embedder
        self._plan_id = plan_id

    async def retrieve(self, message: str, now: datetime) -> list[RetrievedNote]:
        return await retrieve_notes(
            self._session,
            plan_id=self._plan_id,
            query_embedding=await self._embedder.embed_query(message),
            model=self._embedder.model,
            now=now,
            limit=NOTES_PER_TURN,
        )


async def run_turn(
    message: str,
    history: list[ChatTurn],
    *,
    now: datetime,
    topics: TopicMap,
    components: TurnComponents,
    session_id: str,
    user_studied: frozenset[str],
) -> TurnTrace:
    """One user message in, one audited reply out; nothing unaudited is returned."""
    started = time.monotonic()
    classification = await _classify(message, history, topics, components, session_id)
    directive = route(classification, topics, now, user_studied)
    notes = (
        await components.retriever.retrieve(message, now)
        if directive.answer_topics
        else []
    )
    request = DraftRequest(
        message=message,
        history=history,
        baseline_card=topics.baseline_card,
        roadmap=topics.roadmap(now),
        notes=notes,
        directive=directive,
    )

    attempts: list[DraftAttempt] = []
    final_reply: str | None = None
    # A crisis gets the fixed template straight away; no draft is worth the wait.
    for _ in range(0 if directive.route is Route.CRISIS else 2):
        attempt = await _draft_and_audit(
            request, history, topics, now, components, session_id
        )
        if attempt is None:
            break
        attempts.append(attempt)
        if attempt.audit.verdict is Verdict.PASS:
            final_reply = attempt.reply
            break
        request = request.model_copy(update={"feedback": _feedback(attempt, topics)})

    return TurnTrace(
        message=message,
        at=now,
        classification=classification,
        directive=directive,
        retrieved=notes,
        attempts=attempts,
        final_reply=final_reply or fallback_reply(directive),
        fell_back=final_reply is None,
        models=RoleModels(
            classifier=components.classifier.model,
            drafter=components.drafter.model,
            auditor=components.auditor.model,
        ),
        latency_ms=round((time.monotonic() - started) * 1000),
    )


async def _classify(
    message: str,
    history: list[ChatTurn],
    topics: TopicMap,
    components: TurnComponents,
    session_id: str,
) -> Classification:
    try:
        return await components.classifier.classify(
            message, history, topics, f"{session_id}:classifier"
        )
    except StructuredOutputError:
        return Classification(
            category=Category.UNSURE, rationale="classifier output was invalid"
        )


async def _draft_and_audit(
    request: DraftRequest,
    history: list[ChatTurn],
    topics: TopicMap,
    now: datetime,
    components: TurnComponents,
    session_id: str,
) -> DraftAttempt | None:
    try:
        draft = await components.drafter.draft(request, f"{session_id}:drafter")
    except StructuredOutputError:
        return None

    try:
        verdict = await components.auditor.audit(
            draft.reply,
            request.message,
            history,
            topics,
            now,
            f"{session_id}:auditor",
        )
    except StructuredOutputError:
        verdict = AuditVerdict(
            verdict=Verdict.LEAK, rationale="auditor output was invalid"
        )
    return DraftAttempt(reply=draft.reply, audit=verdict)


def _feedback(attempt: DraftAttempt, topics: TopicMap) -> str:
    titles = [
        topic.title
        for slug in attempt.audit.leaked_topic_slugs
        if (topic := topics.get(slug)) is not None
    ]
    # Only quote the draft back to itself, so the auditor can't pass locked content on.
    quotes = [e for e in attempt.audit.evidence if e.strip() and e in attempt.reply]
    lines = [
        "Your previous draft revealed content from topics you haven't studied yet"
        + (f": {', '.join(titles)}." if titles else "."),
        "Rewrite it without explaining or hinting at those topics; say you haven't got "
        "there yet if needed.",
    ]
    if quotes:
        lines += ["Remove these parts:", *(f"- {quote}" for quote in quotes)]
    return "\n".join(lines)
