import json

import httpx2
import pytest

from kindred_llm import Embedder, EmbeddingError


def embedder(vectors: list[list[float]], seen: list[httpx2.Request]) -> Embedder:
    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(
            200,
            json={
                "object": "list",
                "model": "embed-test",
                "data": [
                    {"object": "embedding", "index": i, "embedding": v}
                    for i, v in reversed(list(enumerate(vectors)))
                ],
                "usage": {"prompt_tokens": 1, "total_tokens": 1},
            },
        )

    return Embedder(
        base_url="https://embed.test/v1",
        api_key="key",
        model="embed-test",
        dimensions=2,
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
    )


@pytest.mark.anyio
async def test_documents_are_embedded_verbatim_in_input_order() -> None:
    seen: list[httpx2.Request] = []

    vectors = await embedder([[1.0, 0.0], [0.0, 1.0]], seen).embed_documents(
        ["first", "second"]
    )

    assert vectors == [[1.0, 0.0], [0.0, 1.0]]
    body = json.loads(seen[0].content)
    assert body["model"] == "embed-test"
    assert body["input"] == ["first", "second"]


@pytest.mark.anyio
async def test_queries_carry_the_retrieval_instruction() -> None:
    seen: list[httpx2.Request] = []

    vector = await embedder([[0.5, 0.5]], seen).embed_query("what is IAM?")

    assert vector == [0.5, 0.5]
    [text] = json.loads(seen[0].content)["input"]
    assert text.startswith("Instruct: ")
    assert text.endswith("\nQuery:what is IAM?")


@pytest.mark.anyio
async def test_wrong_dimensions_are_rejected() -> None:
    with pytest.raises(EmbeddingError, match="dimensions"):
        await embedder([[1.0, 0.0, 0.0]], []).embed_documents(["text"])
