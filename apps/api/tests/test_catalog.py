from datetime import UTC, datetime
from pathlib import Path

from kindred_api.catalog import all_locked, as_course, load_catalog

CURRICULA = Path(__file__).parents[3] / "curricula"
NOW = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)


def test_the_catalog_offers_the_hand_written_courses() -> None:
    [aws] = load_catalog(CURRICULA)

    course = as_course(aws)

    assert course.slug == "aws-2week"
    assert len(course.topics) == 14
    assert course.topics[0].day == 1


def test_during_onboarding_every_topic_is_locked() -> None:
    topics = all_locked(load_catalog(CURRICULA), NOW)

    assert topics.unlocked(NOW) == []
    assert len(topics.locked(NOW)) == 14
