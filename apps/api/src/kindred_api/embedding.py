from typing import Protocol


class DocumentEmbedder(Protocol):
    model: str

    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
