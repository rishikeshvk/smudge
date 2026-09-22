import json

import httpx2
import pytest

from kindred_llm import LLMClient


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


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
