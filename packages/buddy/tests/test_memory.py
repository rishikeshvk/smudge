from collections.abc import Callable
from datetime import date

import httpx2
import pytest

from kindred_buddy.memory import MemoryWriter, build_prompt
from kindred_contracts import DayMessage, MemoryBrief, Speaker
from kindred_llm import LLMClient

ScriptedLLM = Callable[[list[str]], tuple[LLMClient, list[httpx2.Request]]]
SentPrompt = Callable[[httpx2.Request], tuple[str, str]]

BRIEF = MemoryBrief(
    buddy_name="Juno",
    day=date(2026, 10, 5),
    conversation=[
        DayMessage(
            speaker=Speaker.BUDDY,
            text="morning. IAM tonight around 19:00, you?",
            scheduled=True,
        ),
        DayMessage(
            speaker=Speaker.USER,
            text="studying late again, work ran over",
            scheduled=False,
        ),
        DayMessage(
            speaker=Speaker.BUDDY, text="oof, same time tomorrow?", scheduled=False
        ),
    ],
    facts=["Studies after work, around 21:00."],
)


def test_prompt_carries_the_day_and_what_is_remembered() -> None:
    prompt = build_prompt(BRIEF)

    assert "- Studies after work, around 21:00." in prompt
    assert "The chat on Monday 05 October:" in prompt
    assert "them: studying late again, work ran over" in prompt


def test_prompt_keeps_the_buddys_own_messages_apart_from_theirs() -> None:
    prompt = build_prompt(BRIEF)

    assert (
        "Juno (you, scheduled message): morning. IAM tonight around 19:00, you?"
        in prompt
    )
    assert "Juno (you): oof, same time tomorrow?" in prompt


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
