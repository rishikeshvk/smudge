from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.config import Settings
from kindred_api.llm_clients import (
    build_memory_writer,
    build_planning,
    build_reflection_components,
    build_study_components,
    build_turn_components,
)
from kindred_api.onboarding import Planning
from kindred_api.reflection import ReflectionComponents
from kindred_api.study import StudyComponents
from kindred_buddy.memory import MemoryWriter
from kindred_contracts import PersonaContext
from kindred_gate import TurnComponents


class LLMRuntime:
    """The LLM settings in effect. Components are built on each use, so settings
    saved from the app apply to the next call without a restart."""

    def __init__(self, base: Settings, settings: Settings) -> None:
        # .env alone, and .env with the app's saved settings on top.
        self.base = base
        self.settings = settings

    def turn_components(
        self, session: AsyncSession, plan_id: int, persona: PersonaContext
    ) -> TurnComponents:
        return build_turn_components(self.settings, session, plan_id, persona)

    def study(self) -> StudyComponents:
        return build_study_components(self.settings)

    def memory(self) -> MemoryWriter:
        return build_memory_writer(self.settings)

    def reflection(self) -> ReflectionComponents:
        return build_reflection_components(self.settings)

    def planning(self) -> Planning:
        return build_planning(self.settings)
