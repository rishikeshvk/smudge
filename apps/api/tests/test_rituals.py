from datetime import UTC, datetime, time
from pathlib import Path

import pytest

from kindred_api.catalog import load_curriculum
from kindred_api.rituals import (
    BuddyNight,
    Retried,
    RitualMessage,
    ask,
    failed_study_share,
    morning,
    night_review,
)
from kindred_contracts import Curriculum, TopicRef
from kindred_gate import Topic, TopicMap
from kindred_gate.jargon import jargon_in

CURRICULUM_PATH = Path(__file__).parents[3] / "curricula" / "aws-2week.yaml"
A = TopicRef(slug="a", title="Topic A", day=3)
B = TopicRef(slug="b", title="Topic B", day=2)


@pytest.fixture(scope="module")
def curriculum() -> Curriculum:
    return load_curriculum(CURRICULUM_PATH)


def every_template(day: int) -> list[RitualMessage]:
    return [
        morning(day, A, B, time(19)),
        morning(day, A, A, time(19)),
        morning(day, A, None, time(19)),
        morning(day, A, B, time(19), Retried(B, worked=True)),
        morning(day, A, B, time(19), Retried(B, worked=False)),
        failed_study_share(day, A),
        ask(day, 1, B, "SHAKY"),
        *(
            night_review(day, A, night, you, streak, gap)
            for night in BuddyNight
            for you in (None, B)
            for streak, gap in ((0, 0), (1, 1), (3, -2))
        ),
    ]


def test_templates_use_no_curriculum_jargon(curriculum: Curriculum) -> None:
    # Everything locked: the fixed wording must hold up even on day 0.
    topics = TopicMap(
        plan_id=0,
        baseline_card=[],
        topics=[
            Topic(
                slug=node.slug,
                day=node.day,
                title=node.title,
                audit_brief="",
                unlock_at=datetime(2027, 1, 1, tzinfo=UTC),
                vocabulary=node.vocabulary,
            )
            for node in curriculum.nodes
        ],
    )
    now = datetime(2026, 1, 1, tzinfo=UTC)
    leaks = [
        f"{word.term!r} in {message.text!r}"
        for day in range(1, 4)
        for message in every_template(day)
        for _, word in jargon_in(message.text, topics, now)
    ]

    assert leaks == []


def test_templates_name_only_the_topics_they_are_given(
    curriculum: Curriculum,
) -> None:
    [first, second, *rest] = curriculum.nodes
    given = TopicRef(slug=first.slug, title=first.title, day=1)
    you = TopicRef(slug=second.slug, title=second.title, day=2)
    texts = [
        morning(1, given, you, time(19)).text,
        night_review(1, given, BuddyNight.STUDIED, you, 1, 0).text,
        failed_study_share(1, given).text,
    ]

    named = [node.title for node in rest for text in texts if node.title in text]

    assert named == []


def test_morning_says_when_the_buddy_studies_and_where_the_user_is() -> None:
    message = morning(1, A, B, time(19))

    assert "Topic A" in message.text and "19:00" in message.text
    assert "yours is Topic B." in message.text
    assert message.card.model_dump()["quick_replies"]


def test_morning_names_a_shared_topic_once() -> None:
    message = morning(1, A, A, time(19))

    assert message.text.count("Topic A") == 1
    assert "same one for you." in message.text


def test_night_review_is_honest_about_the_gap() -> None:
    behind = night_review(4, A, BuddyNight.STUDIED, None, 2, 1).text
    ahead = night_review(4, A, BuddyNight.NOT_YET, B, 3, -2).text

    assert "did you get to yours?" in behind
    assert "you're 1 topic behind me for now." in behind
    assert "you got through Topic B. that's 3 days running." in ahead
    assert "you're 2 topics ahead of me." in ahead
    assert "haven't got to Topic A yet." in ahead


def test_night_review_names_a_shared_topic_once() -> None:
    text = night_review(4, A, BuddyNight.STUDIED, A, 1, 0).text

    assert text.count("Topic A") == 1
    assert "you did it too. first day of a new streak." in text


def test_the_ask_quotes_its_shaky_point() -> None:
    message = ask(2, 7, B, "why regions?")

    assert message.text.endswith("“why regions?”")
    assert message.card.model_dump() == {
        "kind": "ask",
        "note_id": 7,
        "topic": B.model_dump(),
    }
