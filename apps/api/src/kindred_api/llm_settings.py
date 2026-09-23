from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.config import Settings
from kindred_contracts import LLMSettingsUpdate, LLMSettingsView, ModelsPerRole
from kindred_db import LLMSettings

ROLES = ["classifier", "persona", "auditor", "planner", "curator"]


async def load_saved(session: AsyncSession) -> LLMSettings:
    return await session.get(LLMSettings, 1) or LLMSettings(id=1)


async def save(session: AsyncSession, update: LLMSettingsUpdate) -> LLMSettings:
    """Merge an update into what's saved; fields left out keep their value."""
    saved = await load_saved(session)
    if update.base_url is not None:
        saved.base_url = update.base_url
    if update.api_key is not None:
        saved.api_key = update.api_key.get_secret_value()
    if update.models is not None:
        saved.models = update.models.model_dump()
    saved = await session.merge(saved)
    await session.flush()
    return saved


def effective(base: Settings, saved: LLMSettings) -> Settings:
    """.env settings with whatever the user saved in the app on top."""
    models = saved.models or {}
    return base.model_copy(
        update={
            "llm_base_url": saved.base_url or base.llm_base_url,
            "llm_api_key": SecretStr(saved.api_key)
            if saved.api_key
            else base.llm_api_key,
            **{f"llm_model_{role}": models[role] for role in ROLES if role in models},
        }
    )


def view(settings: Settings) -> LLMSettingsView:
    return LLMSettingsView(
        base_url=settings.llm_base_url,
        api_key_set=bool(settings.llm_api_key.get_secret_value()),
        models=ModelsPerRole(
            classifier=settings.llm_model_classifier,
            persona=settings.llm_model_persona,
            auditor=settings.llm_model_auditor,
            planner=settings.llm_model_planner,
            curator=settings.llm_model_curator,
        ),
    )
