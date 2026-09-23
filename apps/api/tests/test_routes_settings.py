from collections.abc import Callable
from datetime import UTC, datetime

import httpx
import pytest
from pydantic import SecretStr

from kindred_api.clock import Clock, FixedClock
from kindred_api.config import get_settings
from kindred_api.dependencies import get_llm
from kindred_api.llm_runtime import LLMRuntime
from kindred_api.main import app
from kindred_api.turn_worker import TurnWorker

ApiClient = Callable[[Clock, TurnWorker | None], httpx.AsyncClient]
NOW = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)
KEY = "sk-never-shown-9f2c"


@pytest.fixture
def runtime() -> LLMRuntime:
    # Port 9 refuses connections, so the connection check fails without a network.
    base = get_settings().model_copy(
        update={"llm_base_url": "http://127.0.0.1:9/v1", "llm_api_key": SecretStr(KEY)}
    )
    runtime = LLMRuntime(base, base)
    app.dependency_overrides[get_llm] = lambda: runtime
    return runtime


@pytest.fixture
def client(api: ApiClient, runtime: LLMRuntime) -> httpx.AsyncClient:
    return api(FixedClock(NOW), None)


@pytest.mark.anyio
async def test_settings_show_the_endpoint_and_models_but_not_the_key(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/settings")

    assert response.json()["base_url"] == "http://127.0.0.1:9/v1"
    assert response.json()["api_key_set"] is True
    assert KEY not in response.text


@pytest.mark.anyio
async def test_saving_applies_at_once_and_the_key_stays_write_only(
    client: httpx.AsyncClient, runtime: LLMRuntime
) -> None:
    models = {
        "classifier": "c",
        "persona": "p",
        "auditor": "a",
        "planner": "pl",
        "curator": "cu",
    }

    response = await client.put(
        "/settings", json={"api_key": "sk-new-key", "models": models}
    )

    assert response.json()["models"] == models
    assert "sk-new-key" not in response.text
    assert runtime.settings.llm_api_key.get_secret_value() == "sk-new-key"
    assert runtime.settings.llm_model_persona == "p"


@pytest.mark.anyio
async def test_an_unreachable_endpoint_fails_the_check_without_details(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post("/settings/test")

    assert response.json()["ok"] is False
    assert response.json()["models"] == []
    assert KEY not in response.text
