from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.config import Settings
from kindred_api.drafter import StubDrafter
from kindred_db import EMBEDDING_DIMENSIONS
from kindred_gate import GatedRetriever, LLMAuditor, LLMClassifier, TurnComponents
from kindred_llm import Embedder, LLMClient


def build_llm(settings: Settings, model: str) -> LLMClient:
    return LLMClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key.get_secret_value(),
        model=model,
    )


def build_embedder(settings: Settings) -> Embedder:
    return Embedder(
        base_url=settings.embed_base_url,
        api_key=settings.embed_api_key.get_secret_value(),
        model=settings.embed_model,
        dimensions=EMBEDDING_DIMENSIONS,
    )


def build_turn_components(
    settings: Settings, session: AsyncSession, plan_id: int
) -> TurnComponents:
    return TurnComponents(
        classifier=LLMClassifier(build_llm(settings, settings.llm_model_classifier)),
        retriever=GatedRetriever(session, build_embedder(settings), plan_id),
        drafter=StubDrafter(build_llm(settings, settings.llm_model_drafter)),
        auditor=LLMAuditor(build_llm(settings, settings.llm_model_auditor)),
    )
