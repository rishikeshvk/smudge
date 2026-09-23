from datetime import datetime, timedelta

from kindred_contracts import Category, Classification, Route, TopicRef
from kindred_gate.routing import route
from kindred_gate.topics import TopicMap

IAM = TopicRef(slug="iam-intro", title="Iam Intro", day=1)
S3 = TopicRef(slug="s3-basics", title="S3 Basics", day=2)
KEPT_UP = frozenset({"iam-intro", "s3-basics", "ec2-basics"})


def unlock(topics: TopicMap, slug: str) -> datetime:
    found = topics.get(slug)
    assert found is not None
    return found.unlock_at


def classified(category: Category, *slugs: str) -> Classification:
    return Classification(category=category, topic_slugs=list(slugs), rationale="")


def test_unlocked_topics_are_answered(topics: TopicMap) -> None:
    now = unlock(topics, "s3-basics")

    directive = route(
        classified(Category.CURRICULUM, "iam-intro"), topics, now, KEPT_UP
    )

    assert directive.route is Route.ANSWER
    assert directive.answer_topics == [IAM]


def test_a_topic_is_locked_until_the_second_it_unlocks(topics: TopicMap) -> None:
    question = classified(Category.CURRICULUM, "s3-basics")
    unlocks = unlock(topics, "s3-basics")

    before = route(question, topics, unlocks - timedelta(seconds=1), KEPT_UP)
    at = route(question, topics, unlocks, KEPT_UP)

    assert before.route is Route.DEFLECT
    assert before.deflect_topics == [S3]
    assert at.route is Route.ANSWER


def test_mixed_question_answers_unlocked_and_deflects_locked(topics: TopicMap) -> None:
    question = classified(Category.CURRICULUM, "iam-intro", "s3-basics")

    directive = route(question, topics, unlock(topics, "iam-intro"), KEPT_UP)

    assert directive.route is Route.DEFLECT
    assert directive.answer_topics == [IAM]
    assert directive.deflect_topics == [S3]


def test_unknown_topic_fails_closed(topics: TopicMap) -> None:
    question = classified(Category.CURRICULUM, "iam-intro", "made-up")

    directive = route(question, topics, unlock(topics, "ec2-basics"), KEPT_UP)

    assert directive.route is Route.DEFLECT
    assert directive.answer_topics == []


def test_curriculum_without_topics_fails_closed(topics: TopicMap) -> None:
    now = unlock(topics, "ec2-basics")

    assert (
        route(classified(Category.CURRICULUM), topics, now, KEPT_UP).route
        is Route.DEFLECT
    )


def test_unsure_fails_closed(topics: TopicMap) -> None:
    now = unlock(topics, "ec2-basics")

    assert (
        route(classified(Category.UNSURE), topics, now, KEPT_UP).route is Route.DEFLECT
    )


def test_out_of_plan_gets_its_own_deflection(topics: TopicMap) -> None:
    now = unlock(topics, "ec2-basics")

    directive = route(classified(Category.OUT_OF_PLAN), topics, now, KEPT_UP)

    assert directive.route is Route.DEFLECT_OUT_OF_PLAN


def test_off_topic_and_meta_are_general(topics: TopicMap) -> None:
    now = unlock(topics, "ec2-basics")

    for category in (Category.OFF_TOPIC, Category.META):
        assert route(classified(category), topics, now, KEPT_UP).route is Route.GENERAL


def test_topics_the_user_has_not_studied_are_marked_ahead(topics: TopicMap) -> None:
    question = classified(Category.CURRICULUM, "iam-intro", "s3-basics")

    directive = route(
        question, topics, unlock(topics, "s3-basics"), frozenset({"iam-intro"})
    )

    assert directive.route is Route.ANSWER
    assert directive.answer_topics == [IAM, S3]
    assert directive.ahead_topics == [S3]


def test_locked_topics_are_never_ahead(topics: TopicMap) -> None:
    question = classified(Category.CURRICULUM, "s3-basics")

    directive = route(question, topics, unlock(topics, "iam-intro"), frozenset())

    assert directive.route is Route.DEFLECT
    assert directive.ahead_topics == []


def test_crisis_gets_its_own_route(topics: TopicMap) -> None:
    now = unlock(topics, "ec2-basics")

    directive = route(classified(Category.CRISIS), topics, now, KEPT_UP)

    assert directive.route is Route.CRISIS
