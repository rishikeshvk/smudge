import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from kindred_api.main import app
from kindred_contracts import (
    ChatTurn,
    RetrievedNote,
    RoadmapEntry,
    StudyNote,
    TopicRef,
    TurnTrace,
)

APP_CONTRACTS: list[type[BaseModel]] = [
    ChatTurn,
    RetrievedNote,
    RoadmapEntry,
    StudyNote,
    TopicRef,
    TurnTrace,
]


def openapi_with_contracts() -> dict[str, Any]:
    document = app.openapi()
    # No endpoint returns these until M2, so the app's types would miss them.
    _, contracts = models_json_schema(
        [(model, "serialization") for model in APP_CONTRACTS],
        ref_template="#/components/schemas/{model}",
    )
    schemas = document.setdefault("components", {}).setdefault("schemas", {})
    schemas.update(contracts["$defs"])
    return document


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the app's OpenAPI schema.")
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    args.out.write_text(json.dumps(openapi_with_contracts(), indent=2) + "\n")


if __name__ == "__main__":
    main()
