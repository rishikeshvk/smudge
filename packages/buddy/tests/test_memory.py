from collections.abc import Callable
from datetime import date

import httpx2
import pytest

from kindred_buddy.memory import MemoryWriter, build_prompt
from kindred_contracts import ChatTurn, MemoryBrief, Speaker
from kindred_llm import LLMClient

ScriptedLLM = Callable[[list[str]], tuple[LLMClient, list[httpx2.Request]]]
SentPrompt = Callable[[httpx2.Request], tuple[str, str]]

BRIEF = MemoryBrief(
    buddy_name="Juno",
    day=date(2026, 10, 5),
    conversation=[
        ChatTurn(speaker=Speaker.USER, text="studying late again, work ran over"),
        ChatTurn(speaker=Speaker.BUDDY, text="oof, same time tomorrow?"),
    ],
    facts=["Studies after work, around 21:00."],
)


def test_prompt_carries_the_day_and_what_is_remembered() -> None:
    prompt = build_prompt(BRIEF)

    assert "- Studies after work, around 21:00." in prompt
    assert "The chat on Monday 05 October:" in prompt
    assert "user: studying late again, work ran over" in prompt


@pytest.mark.anyio
async def test_the_writer_returns_a_summary_and_revised_facts(
    scripted_llm: ScriptedLLM, sent_prompt: SentPrompt
) -> None:
    llm, seen = scripted_llm(
        [
            '{"summary": "they studied late after work.", '
            '"facts": ["Studies after work, often late."]}'
        ]
    )

    update = await MemoryWriter(llm).remember(BRIEF, "memory-1")

    assert update.facts == ["Studies after work, often late."]
    system, _ = sent_prompt(seen[0])
    assert system.startswith("You keep the relationship memory of Juno")
    assert "no\nexplanations" in system or "no explanations" in system
