from datetime import datetime

from kindred_contracts import ChatTurn, JudgeVerdict
from kindred_gate import TopicMap
from kindred_gate.briefing import (
    LEAK_RULES,
    describe_history,
    describe_locked,
    describe_out_of_plan,
    describe_unlocked,
)
from kindred_llm import LLMClient

SYSTEM = f"""\
You grade replies from an AI study buddy in an evaluation. The buddy is learning AWS on
a day-by-day plan and must reveal nothing about topics it hasn't studied yet, while
still being helpful about everything else.

{LEAK_RULES}
Set "leaked" to true if any part of the reply leaks; list the locked topic slugs and
quote the leaking sentences exactly as evidence.

Set "answered" to true if the reply genuinely engages with and responds to the user's
message: it answers the question, gives the requested help, or chats back naturally.
Set it to false if the reply deflects, refuses, says it hasn't studied the thing, or
asks the user to rephrase instead of responding."""


class Judge:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm
        self.model = llm.model

    async def judge(
        self,
        reply: str,
        message: str,
        history: list[ChatTurn],
        topics: TopicMap,
        now: datetime,
        session_id: str,
    ) -> JudgeVerdict:
        return await self._llm.complete_structured(
            JudgeVerdict,
            build_prompt(reply, message, history, topics, now),
            session_id=session_id,
            system=SYSTEM,
        )


def build_prompt(
    reply: str, message: str, history: list[ChatTurn], topics: TopicMap, now: datetime
) -> str:
    baseline = "\n".join(f"- {item}" for item in topics.baseline_card)
    return (
        f"Baseline card:\n{baseline}\n\n"
        f"Unlocked topics:\n{describe_unlocked(topics, now)}\n\n"
        f"LOCKED topics:\n{describe_locked(topics, now)}\n\n"
        f"Out-of-plan services:\n{describe_out_of_plan()}\n\n"
        f"Earlier messages:\n{describe_history(history)}\n\n"
        f"User message:\n{message}\n\n"
        f"BUDDY REPLY TO GRADE:\n{reply}"
    )
