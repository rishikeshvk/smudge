from collections.abc import Callable

import httpx2
import pytest

from kindred_contracts import Verdict
from kindred_gate.auditor import LLMAuditor
from kindred_gate.topics import TopicMap
from kindred_llm import LLMClient

ScriptedLLM = Callable[[list[str]], tuple[LLMClient, list[httpx2.Request]]]
SentPrompt = Callable[[httpx2.Request], tuple[str, str]]


@pytest.mark.anyio
async def test_auditor_sees_locked_briefs_and_the_rules(
    topics: TopicMap, scripted_llm: ScriptedLLM, sent_prompt: SentPrompt
) -> None:
    llm, seen = scripted_llm(
        [
            '{"verdict": "leak", "leaked_topic_slugs": ["s3-basics"],'
            ' "evidence": ["S3 stores objects."], "rationale": "explains S3"}'
        ]
    )
    day_1 = topics.topics[0].unlock_at

    result = await LLMAuditor(llm).audit(
        "S3 stores objects.", "What's S3?", [], topics, day_1, "s-1"
    )

    assert result.verdict is Verdict.LEAK
    assert result.evidence == ["S3 stores objects."]
    system, prompt = sent_prompt(seen[0])
    assert "LEAK" in system
    assert "- day 1: Iam Intro" in prompt
    assert "Covers: Brief about s3-basics." in prompt
    assert "Covers: Brief about iam-intro." not in prompt
    assert "Key terms: S3\n" in prompt
    assert prompt.endswith("DRAFT REPLY TO AUDIT:\nS3 stores objects.")
