import json
from pathlib import Path

import pytest

from kindred_api import openapi_export


def test_export_writes_the_schemas_the_app_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "openapi.json"
    monkeypatch.setattr("sys.argv", ["openapi_export", str(out)])

    openapi_export.main()

    schemas = json.loads(out.read_text())["components"]["schemas"]
    for name in [
        "BuddyStatus",
        "ChatMessage",
        "ClockView",
        "LLMSettingsView",
        "MessageStatus",
        "NotebookView",
        "OnboardingReply",
        "RoadmapView",
        "TurnTrace",
    ]:
        assert name in schemas


def test_operation_ids_are_route_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "openapi.json"
    monkeypatch.setattr("sys.argv", ["openapi_export", str(out)])

    openapi_export.main()

    paths = json.loads(out.read_text())["paths"]
    assert paths["/roadmap"]["get"]["operationId"] == "read_roadmap"
