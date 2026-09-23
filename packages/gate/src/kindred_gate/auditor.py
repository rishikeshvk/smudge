from datetime import datetime

from kindred_contracts import AuditVerdict, ChatTurn
from kindred_gate.briefing import (
    LEAK_RULES,
    describe_history,
    describe_locked,
    describe_out_of_plan,
    describe_unlocked,
)
from kindred_gate.topics import TopicMap
from kindred_llm import LLMClient

SYSTEM = f"""\
You audit a draft reply from an AI study buddy before it is sent. The buddy is learning
AWS on a day-by-day plan and must reveal nothing about topics it hasn't studied yet.

{LEAK_RULES}
Return verdict "leak" if any part of the draft leaks, otherwise "pass". For a leak, list
the locked topic slugs it reveals and quote the offending sentences EXACTLY as they
appear in the draft as evidence."""


NOTE_SYSTEM = f"""\
You audit a study note an AI study buddy wrote for its own notebook, which the user
will read. The buddy is learning AWS on a day-by-day plan; the note must cover only
topics unlocked so far and reveal nothing about topics it hasn't studied yet.

{LEAK_RULES}
Return verdict "leak" if any part of the note leaks, otherwise "pass". For a leak, list
the locked topic slugs it reveals and quote the offending sentences EXACTLY as they
appear in the note as evidence."""


class LLMAuditor:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self.model = llm.model

    async def audit(
        self,
        draft: str,
        message: str,
        history: list[ChatTurn],
        topics: TopicMap,
        now: datetime,
        session_id: str,
    ) -> AuditVerdict:
        return await self._llm.complete_structured(
            AuditVerdict,
            build_prompt(draft, message, history, topics, now),
            session_id=session_id,
            system=SYSTEM,
        )

    async def audit_note(
        self, note: str, topics: TopicMap, now: datetime, session_id: str
    ) -> AuditVerdict:
        return await self._llm.complete_structured(
            AuditVerdict,
            build_note_prompt(note, topics, now),
            session_id=session_id,
            system=NOTE_SYSTEM,
        )


def build_prompt(
    draft: str, message: str, history: list[ChatTurn], topics: TopicMap, now: datetime
) -> str:
    return (
        f"{_what_is_locked(topics, now)}\n\n"
        f"Earlier messages:\n{describe_history(history)}\n\n"
        f"User message:\n{message}\n\n"
        f"DRAFT REPLY TO AUDIT:\n{draft}"
    )


def build_note_prompt(note: str, topics: TopicMap, now: datetime) -> str:
    return f"{_what_is_locked(topics, now)}\n\nNOTE TO AUDIT:\n{note}"


def _what_is_locked(topics: TopicMap, now: datetime) -> str:
    baseline = "\n".join(f"- {item}" for item in topics.baseline_card)
    return (
        f"Baseline card:\n{baseline}\n\n"
        f"Unlocked topics:\n{describe_unlocked(topics, now)}\n\n"
        f"LOCKED topics:\n{describe_locked(topics, now)}\n\n"
        f"Out-of-plan services:\n{describe_out_of_plan()}"
    )
