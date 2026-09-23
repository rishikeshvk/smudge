from kindred_api.config import Settings
from kindred_db import EMBEDDING_DIMENSIONS
from kindred_llm import Embedder


def build_embedder(settings: Settings) -> Embedder:
    return Embedder(
        base_url=settings.embed_base_url,
        api_key=settings.embed_api_key.get_secret_value(),
        model=settings.embed_model,
        dimensions=EMBEDDING_DIMENSIONS,
    )
