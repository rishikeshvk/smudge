from fastapi import APIRouter

from kindred_api.dependencies import LLMRuntimeDep, SessionDep
from kindred_api.llm_clients import build_llm
from kindred_api.llm_settings import effective, save, view
from kindred_contracts import ConnectionCheck, LLMSettingsUpdate, LLMSettingsView
from kindred_llm import LLMUnavailableError, RateLimitedError

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def read_settings(runtime: LLMRuntimeDep) -> LLMSettingsView:
    return view(runtime.settings)


@router.put("")
async def update_settings(
    body: LLMSettingsUpdate, session: SessionDep, runtime: LLMRuntimeDep
) -> LLMSettingsView:
    saved = await save(session, body)
    await session.commit()
    runtime.settings = effective(runtime.base, saved)
    return view(runtime.settings)


@router.post("/test")
async def test_connection(runtime: LLMRuntimeDep) -> ConnectionCheck:
    """Lists the endpoint's models: proves the URL and key work without spending."""
    client = build_llm(runtime.settings, runtime.settings.llm_model_persona)
    try:
        models = await client.list_models()
    except RateLimitedError:
        return ConnectionCheck(ok=False, models=[], detail="usage limit reached")
    except LLMUnavailableError:
        # Generic on purpose: provider errors are never echoed back to the app.
        return ConnectionCheck(
            ok=False,
            models=[],
            detail="couldn't reach the endpoint, or it refused the key",
        )
    return ConnectionCheck(ok=True, models=models, detail=None)
