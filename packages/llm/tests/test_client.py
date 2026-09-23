import json

import httpx2
import pytest
from pydantic import BaseModel

from kindred_llm import LLMClient, StructuredOutputError


@pytest.mark.anyio
async def test_complete_sends_model_and_key_and_returns_reply() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(
            200,
            json={
                "id": "1",
                "object": "chat.completion",
                "created": 0,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": "hi there"},
                    }
                ],
            },
        )

    client = LLMClient(
        base_url="https://llm.test/v1",
        api_key="sk-test",
        model="test-model",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
    )

    reply = await client.complete("hello", session_id="chat-1", system="be brief")

    assert reply == "hi there"
    request = seen[0]
    assert str(request.url) == "https://llm.test/v1/chat/completions"
    assert request.headers["authorization"] == "Bearer sk-test"
    assert request.headers["x-opencode-session"] == "chat-1"
    assert request.headers["user-agent"].startswith("kindred/")
    body = json.loads(request.content)
    assert body["model"] == "test-model"
    assert body["messages"] == [
        {"role": "system", "content": "be brief"},
        {"role": "user", "content": "hello"},
    ]


class Verdict(BaseModel):
    verdict: str
    score: int


def scripted(replies: list[str], seen: list[httpx2.Request]) -> LLMClient:
    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(
            200,
            json={
                "id": str(len(seen)),
                "object": "chat.completion",
                "created": 0,
                "model": "test-model",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {
                            "role": "assistant",
                            "content": replies[len(seen) - 1],
                        },
                    }
                ],
            },
        )

    return LLMClient(
        base_url="https://llm.test/v1",
        api_key="sk-test",
        model="test-model",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
    )


@pytest.mark.anyio
async def test_structured_reply_is_parsed_and_schema_sent() -> None:
    seen: list[httpx2.Request] = []
    client = scripted(['{"verdict": "pass", "score": 3}'], seen)

    result = await client.complete_structured(
        Verdict, "judge this", session_id="s", system="You judge."
    )

    assert result == Verdict(verdict="pass", score=3)
    system = json.loads(seen[0].content)["messages"][0]["content"]
    assert system.startswith("You judge.")
    assert '"score"' in system


@pytest.mark.anyio
async def test_fenced_json_is_accepted() -> None:
    client = scripted(['Sure!\n```json\n{"verdict": "leak", "score": 1}\n```'], [])

    result = await client.complete_structured(
        Verdict, "judge this", session_id="s", system="You judge."
    )

    assert result.verdict == "leak"


@pytest.mark.anyio
async def test_invalid_reply_is_retried_with_the_error() -> None:
    seen: list[httpx2.Request] = []
    client = scripted(['{"verdict": "pass"}', '{"verdict": "pass", "score": 2}'], seen)

    result = await client.complete_structured(
        Verdict, "judge this", session_id="s", system="You judge."
    )

    assert result.score == 2
    retry = json.loads(seen[1].content)["messages"]
    assert retry[-2] == {"role": "assistant", "content": '{"verdict": "pass"}'}
    assert "score" in retry[-1]["content"]


@pytest.mark.anyio
async def test_gives_up_after_three_invalid_replies() -> None:
    seen: list[httpx2.Request] = []
    client = scripted(["nope", "still nope", "no"], seen)

    with pytest.raises(StructuredOutputError, match="Verdict"):
        await client.complete_structured(
            Verdict, "judge this", session_id="s", system="You judge."
        )
    assert len(seen) == 3
