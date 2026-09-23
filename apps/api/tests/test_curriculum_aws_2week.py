from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from kindred_api.seed import load_curriculum
from kindred_contracts import Curriculum
from kindred_gate import Topic, TopicMap
from kindred_gate.jargon import jargon_in

CURRICULUM_PATH = Path(__file__).parents[3] / "curricula" / "aws-2week.yaml"
MAX_NOTE_WORDS = 400

SPEC_TITLES = [
    ("cloud-basics", "What AWS is & global infrastructure"),
    ("account-billing", "Your AWS account, root user & billing"),
    ("iam-intro", "Shared responsibility & IAM overview"),
    ("iam-users-groups", "IAM users, groups & credentials"),
    ("iam-policies", "IAM policies & policy evaluation"),
    ("iam-roles", "IAM roles & Identity Center"),
    ("s3-basics", "S3 fundamentals"),
    ("s3-access", "S3 access control"),
    ("s3-encryption-versioning", "S3 encryption & versioning"),
    ("s3-classes-sharing", "S3 storage classes & sharing"),
    ("ec2-basics", "EC2 fundamentals"),
    ("ec2-network-access", "EC2 networking & connecting"),
    ("ec2-storage-lifecycle", "EC2 storage & instance lifecycle"),
    ("ec2-roles-metadata", "User data, instance metadata & roles for EC2"),
]


@pytest.fixture(scope="module")
def curriculum() -> Curriculum:
    return load_curriculum(CURRICULUM_PATH)


def topic_map(curriculum: Curriculum) -> TopicMap:
    # Day N unlocks at N o'clock, so "now" at hour N means days 1..N are unlocked.
    return TopicMap(
        plan_id=0,
        baseline_card=curriculum.baseline_card,
        topics=[
            Topic(
                slug=node.slug,
                day=node.day,
                title=node.title,
                audit_brief=node.audit_brief,
                unlock_at=at_day(node.day),
                vocabulary=node.vocabulary,
            )
            for node in curriculum.nodes
        ],
    )


def at_day(day: int) -> datetime:
    return datetime(2026, 10, 1, tzinfo=UTC) + timedelta(hours=day)


def test_curriculum_matches_the_spec_topics(curriculum: Curriculum) -> None:
    assert [(n.slug, n.title) for n in curriculum.nodes] == SPEC_TITLES


def test_notes_are_short_enough_to_embed_whole(curriculum: Curriculum) -> None:
    for node in curriculum.nodes:
        for note in node.notes:
            assert len(note.body.split()) <= MAX_NOTE_WORDS, node.slug


def test_notes_never_use_later_topics_jargon(curriculum: Curriculum) -> None:
    leaks = [
        f"day {node.day} note uses {word.term!r} from {later.slug}"
        for node in curriculum.nodes
        for note in node.notes
        for later, word in jargon_in(
            " ".join([note.body, *note.shaky]), topic_map(curriculum), at_day(node.day)
        )
    ]
    assert leaks == []


def test_baseline_card_uses_no_aws_jargon(curriculum: Curriculum) -> None:
    card = " ".join(curriculum.baseline_card)
    leaks = [
        f"{word.term!r} from {topic.slug}"
        for topic, word in jargon_in(card, topic_map(curriculum), at_day(0))
    ]
    assert leaks == []
