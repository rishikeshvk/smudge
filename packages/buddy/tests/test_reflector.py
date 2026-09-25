from collections.abc import Callable

import httpx2
import pytest

from kindred_buddy.reflector import Reflector, build_prompt
from kindred_contracts import (
    ChatTurn,
    ReflectionBrief,
    SourceExcerpt,
    Speaker,
    TopicRef,
)
from kindred_llm import LLMClient

ScriptedLLM = Callable[[list[str]], tuple[LLMClient, list[httpx2.Request]]]
SentPrompt = Callable[[httpx2.Request], tuple[str, str]]

BRIEF = ReflectionBrief(
    plan_title="AWS fundamentals in two weeks",
    topic=TopicRef(slug="cloud-basics", title="What AWS is", day=1),
    open_shaky=["why are AZ letters shuffled per account?"],
    exchanges=[
        ChatTurn(speaker=Speaker.USER, text="they shuffle them so load spreads out"),
        ChatTurn(speaker=Speaker.BUDDY, text="ohh, that would make sense"),
    ],
    sources=[
        SourceExcerpt(
            url="https://docs.test/az",
            title="AZ IDs",
            text="Names are mapped per account to spread resources across zones.",
        )
    ],
)


def test_prompt_carries_the_points_the_chat_and_the_sources() -> None:
    prompt = build_prompt(BRIEF)

    assert "- why are AZ letters shuffled per account?" in prompt
    assert "them: they shuffle them so load spreads out" in prompt
    assert "you: ohh, that would make sense" in prompt
    assert "Names are mapped per account" in prompt


@pytest.mark.anyio
async def test_the_reflector_returns_what_was_sorted(
    scripted_llm: ScriptedLLM, sent_prompt: SentPrompt
) -> None:
    llm, seen = scripted_llm(
        [
            '{"points": [{"shaky": "why are AZ letters shuffled per account?", '
            '"sorted": true, "insight": "the letters are mapped per account so '
            'everyone does not pile into the same zone"}]}'
        ]
    )

    reflection = await Reflector(llm).reflect(BRIEF, "reflect-1")

    [point] = reflection.points
    assert point.sorted and point.insight.startswith("the letters")
    system, _ = sent_prompt(seen[0])
    assert '"AWS fundamentals in two weeks"' in system
    assert "the topic's sources back their explanation up" in system
