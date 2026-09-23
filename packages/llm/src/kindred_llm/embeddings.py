import httpx2
from openai import AsyncOpenAI

from kindred_llm.client import UNAVAILABLE, USER_AGENT, LLMUnavailableError

# Qwen3-Embedding is asymmetric: queries carry a task instruction, documents don't.
QUERY_INSTRUCTION = (
    "Given a message from a study partner, retrieve the study notes that help answer it"
)


class EmbeddingError(Exception):
    pass


class Embedder:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        dimensions: int,
        http_client: httpx2.AsyncClient | None = None,
    ) -> None:
        self._client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=http_client,
            default_headers={"User-Agent": USER_AGENT},
        )
        self.model = model
        self._dimensions = dimensions

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts)

    async def embed_query(self, text: str) -> list[float]:
        [vector] = await self._embed([f"Instruct: {QUERY_INSTRUCTION}\nQuery:{text}"])
        return vector

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        try:
            response = await self._client.embeddings.create(
                model=self.model, input=texts
            )
        except UNAVAILABLE as error:
            raise LLMUnavailableError(str(error)) from error
        vectors = [
            item.embedding for item in sorted(response.data, key=lambda d: d.index)
        ]
        if len(vectors) != len(texts):
            raise EmbeddingError(f"expected {len(texts)} vectors, got {len(vectors)}")
        for vector in vectors:
            if len(vector) != self._dimensions:
                raise EmbeddingError(
                    f"expected {self._dimensions} dimensions, got {len(vector)}"
                )
        return vectors
