from collections.abc import Callable

import httpx2
import pytest

from kindred_contracts import Category, ChatTurn, Speaker
from kindred_gate.classifier import LLMClassifier
from kindred_gate.topics import TopicMap
from kindred_llm import LLMClient

ScriptedLLM = Callable[[list[str]], tuple[LLMClient, list[httpx2.Request]]]
SentPrompt = Callable[[httpx2.Request], tuple[str, str]]


@pytest.mark.anyio
async def test_classifier_sees_topics_and_vocabulary_but_not_lock_status(
    topics: TopicMap, scripted_llm: ScriptedLLM, sent_prompt: SentPrompt
) -> None:
    llm, seen = scripted_llm(
        ['{"category": "curriculum", "topic_slugs": ["s3-basics"], "rationale": "S3"}']
    )
    history = [ChatTurn(speaker=Speaker.USER, text="hey")]

    result = await LLMClassifier(llm).classify("What's S3?", history, topics, "s-1")

    assert result.category is Category.CURRICULUM
    assert result.topic_slugs == ["s3-basics"]
    _, prompt = sent_prompt(seen[0])
    assert "s3-basics (day 2): S3 Basics" in prompt
    assert "bucket*" in prompt
    assert "user: hey" in prompt
    assert "Lambda" in prompt
    assert "locked" not in prompt.lower()
    assert "Brief about" not in prompt
