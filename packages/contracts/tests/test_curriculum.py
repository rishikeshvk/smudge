from typing import Any

import pytest
from pydantic import ValidationError

from kindred_contracts import Curriculum


def node(slug: str, day: int, prerequisites: list[str] | None = None) -> dict[str, Any]:
    return {
        "slug": slug,
        "day": day,
        "title": slug.title(),
        "prerequisites": prerequisites or [],
        "audit_brief": "What this topic covers.",
        "vocabulary": [{"term": slug, "kind": "term"}],
        "notes": [
            {
                "body": "My notes.",
                "shaky": ["Not sure about this part."],
                "sources": ["https://docs.aws.amazon.com/"],
            }
        ],
    }


def curriculum(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {
        "slug": "test",
        "title": "Test",
        "study_time": "19:00",
        "baseline_card": ["AWS is Amazon's cloud."],
        "nodes": list(nodes),
    }


def test_valid_topic_graph_is_accepted() -> None:
    parsed = Curriculum.model_validate(
        curriculum(node("first", 1), node("second", 2, ["first"]))
    )

    assert [n.slug for n in parsed.nodes] == ["first", "second"]


def test_repeated_day_is_rejected() -> None:
    with pytest.raises(ValidationError, match="no gaps or repeats"):
        Curriculum.model_validate(curriculum(node("first", 1), node("second", 1)))


def test_gap_in_days_is_rejected() -> None:
    with pytest.raises(ValidationError, match="no gaps or repeats"):
        Curriculum.model_validate(curriculum(node("first", 1), node("third", 3)))


def test_duplicate_slug_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unique"):
        Curriculum.model_validate(curriculum(node("same", 1), node("same", 2)))


def test_unknown_prerequisite_is_rejected() -> None:
    with pytest.raises(ValidationError, match="unknown prerequisite"):
        Curriculum.model_validate(curriculum(node("first", 1, ["missing"])))


def test_prerequisite_on_a_later_day_is_rejected() -> None:
    with pytest.raises(ValidationError, match="earlier day"):
        Curriculum.model_validate(
            curriculum(node("first", 1, ["second"]), node("second", 2))
        )
