from datetime import UTC, datetime

from kindred_contracts import SortedPoint, still_shaky


def test_still_shaky_leaves_out_what_the_user_helped_sort_out() -> None:
    sorted_points = [
        SortedPoint(
            shaky="why regions?",
            insight="failures stay in one",
            sorted_at=datetime(2026, 10, 2, tzinfo=UTC),
        )
    ]

    assert still_shaky(["why regions?", "what's an AZ?"], sorted_points) == [
        "what's an AZ?"
    ]
