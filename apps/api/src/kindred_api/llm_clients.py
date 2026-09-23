from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.catalog import load_catalog
from kindred_api.config import Settings
from kindred_api.onboarding import Planning
from kindred_api.study import StudyComponents
from kindred_buddy.curator import Curator
from kindred_buddy.memory import MemoryWriter
from kindred_buddy.persona import Persona
from kindred_buddy.planner import Planner
from kindred_contracts import PersonaContext
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
    settings: Settings,
    session: AsyncSession,
    plan_id: int,
    persona: PersonaContext,
) -> TurnComponents:
    return TurnComponents(
        classifier=LLMClassifier(build_llm(settings, settings.llm_model_classifier)),
        retriever=GatedRetriever(session, build_embedder(settings), plan_id),
        drafter=Persona(build_llm(settings, settings.llm_model_persona), persona),
        auditor=LLMAuditor(build_llm(settings, settings.llm_model_auditor)),
    )


def build_study_components(settings: Settings) -> StudyComponents:
    return StudyComponents(
        curator=Curator(build_llm(settings, settings.llm_model_curator)),
        auditor=LLMAuditor(build_llm(settings, settings.llm_model_auditor)),
        embedder=build_embedder(settings),
    )


def build_memory_writer(settings: Settings) -> MemoryWriter:
    # Part of the nightly batch, so it runs on the Curator's model.
    return MemoryWriter(build_llm(settings, settings.llm_model_curator))


def build_planning(settings: Settings) -> Planning:
    return Planning(
        courses=load_catalog(settings.curricula_dir),
        planner=Planner(build_llm(settings, settings.llm_model_planner)),
        auditor=LLMAuditor(build_llm(settings, settings.llm_model_auditor)),
    )
