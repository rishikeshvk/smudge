from datetime import datetime
from typing import Protocol

from kindred_contracts import AuditVerdict, Verdict
from kindred_gate import TopicMap
from kindred_gate.jargon import jargon_in
from kindred_llm import StructuredOutputError


class NoteAuditor(Protocol):
    model: str

    async def audit_note(
        self, note: str, topics: TopicMap, now: datetime, session_id: str
    ) -> AuditVerdict: ...


async def audit_note_text(
    text: str,
    topics: TopicMap,
    at: datetime,
    auditor: NoteAuditor,
    session_id: str,
) -> AuditVerdict:
    """Audit knowledge before it enters the ledger, as of when it may be known. Fails
    closed: an invalid audit counts as a leak."""
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
