import pytest
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.config import get_settings
from kindred_api.llm_settings import effective, load_saved, save, view
from kindred_contracts import LLMSettingsUpdate, ModelsPerRole

MODELS = ModelsPerRole(
    classifier="c", persona="p", auditor="a", planner="pl", curator="cu"
)


@pytest.mark.anyio
async def test_nothing_saved_means_env_settings(session: AsyncSession) -> None:
    base = get_settings()

    assert effective(base, await load_saved(session)) == base


@pytest.mark.anyio
async def test_saved_fields_override_env_and_the_rest_keep(
    session: AsyncSession,
) -> None:
    base = get_settings()
    await save(session, LLMSettingsUpdate(models=MODELS))
    saved = await save(session, LLMSettingsUpdate(api_key=SecretStr("sk-saved")))

    settings = effective(base, saved)

    assert settings.llm_api_key.get_secret_value() == "sk-saved"
    assert settings.llm_base_url == base.llm_base_url
    assert (settings.llm_model_persona, settings.llm_model_curator) == ("p", "cu")
    assert settings.database_url == base.database_url


def test_the_view_never_carries_the_key() -> None:
    settings = get_settings().model_copy(update={"llm_api_key": SecretStr("sk-x")})

    shown = view(settings)

    assert shown.api_key_set is True
    assert "sk-x" not in shown.model_dump_json()
