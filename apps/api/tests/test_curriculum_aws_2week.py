import re
from pathlib import Path

import pytest

from kindred_api.seed import load_curriculum
from kindred_contracts import Curriculum, TopicNode, VocabularyKind, VocabularyTerm

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


def mentions(text: str, word: VocabularyTerm) -> bool:
    # Abbreviations and API names are case-sensitive: "SG" is jargon, "sg" isn't.
    exact = {VocabularyKind.ABBREVIATION, VocabularyKind.API_NAME}
    flags = 0 if word.kind in exact else re.I
    pattern = rf"(?<![\w-]){re.escape(word.term)}(?![\w-])"
    return re.search(pattern, text, flags) is not None


def locked_jargon(
    curriculum: Curriculum, day: int
) -> list[tuple[TopicNode, VocabularyTerm]]:
    # Titles are public, and a term taught by day `day` is known even if a later
    # topic lists it too.
    known = {
        word.term.lower()
        for node in curriculum.nodes
        if node.day <= day
        for word in node.vocabulary
    }
    return [
        (node, word)
        for node in curriculum.nodes
        if node.day > day
        for word in node.vocabulary
        if not word.everyday
        and word.term.lower() not in known
        and not mentions(node.title, word)
    ]


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
        for later, word in locked_jargon(curriculum, node.day)
        if mentions(" ".join([note.body, *note.shaky]), word)
    ]
    assert leaks == []


def test_baseline_card_uses_no_aws_jargon(curriculum: Curriculum) -> None:
    card = " ".join(curriculum.baseline_card)
    leaks = [
        f"{word.term!r} from {node.slug}"
        for node, word in locked_jargon(curriculum, 0)
        if mentions(card, word)
    ]
    assert leaks == []
