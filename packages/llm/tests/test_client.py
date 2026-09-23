import json

import httpx2
import pytest
from pydantic import BaseModel

from kindred_llm import (
    LLMClient,
    LLMUnavailableError,
    RateLimitedError,
    StructuredOutputError,
)


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


@pytest.mark.anyio
async def test_usage_limit_is_reported_as_rate_limited() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        # retry-after-ms keeps the SDK's own retries instant.
        return httpx2.Response(
            429,
            headers={"retry-after-ms": "0"},
            json={"error": {"message": "usage limit reached"}},
        )

    client = LLMClient(
        base_url="https://llm.test/v1",
        api_key="sk-test",
        model="test-model",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
    )

    with pytest.raises(RateLimitedError, match="usage limit"):
        await client.complete("hello", session_id="s")


def failing_client(handler: httpx2.MockTransport) -> LLMClient:
    return LLMClient(
        base_url="https://llm.test/v1",
        api_key="sk-test",
        model="test-model",
        http_client=httpx2.AsyncClient(transport=handler),
    )


@pytest.mark.anyio
async def test_rate_limits_count_as_unavailable() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(429, headers={"retry-after-ms": "0"}, json={})

    with pytest.raises(LLMUnavailableError):
        await failing_client(httpx2.MockTransport(handler)).complete(
            "hello", session_id="s"
        )


@pytest.mark.anyio
async def test_server_errors_and_bad_keys_are_unavailable() -> None:
    for status in (401, 403, 503):

        def handler(request: httpx2.Request, status: int = status) -> httpx2.Response:
            return httpx2.Response(status, headers={"retry-after-ms": "0"}, json={})

        with pytest.raises(LLMUnavailableError):
            await failing_client(httpx2.MockTransport(handler)).complete(
                "hello", session_id="s"
            )


@pytest.mark.anyio
async def test_an_unreachable_endpoint_is_unavailable() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("connection refused")

    with pytest.raises(LLMUnavailableError):
        await failing_client(httpx2.MockTransport(handler)).complete(
            "hello", session_id="s"
        )


@pytest.mark.anyio
async def test_models_are_listed_for_a_connection_check() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.url.path == "/v1/models"
        return httpx2.Response(
            200,
            json={
                "object": "list",
                "data": [
                    {"id": "glm-5.3", "object": "model", "created": 0, "owned_by": "x"},
                    {"id": "kimi-k3", "object": "model", "created": 0, "owned_by": "x"},
                ],
            },
        )

    client = failing_client(httpx2.MockTransport(handler))

    assert await client.list_models() == ["glm-5.3", "kimi-k3"]


@pytest.mark.anyio
async def test_a_refused_key_fails_the_connection_check() -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(401, json={"error": {"message": "bad key"}})

    with pytest.raises(LLMUnavailableError):
        await failing_client(httpx2.MockTransport(handler)).list_models()
