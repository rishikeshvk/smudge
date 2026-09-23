from datetime import UTC, datetime, timedelta

import pytest

from kindred_contracts import VocabularyKind, VocabularyTerm
from kindred_gate.topics import Topic, TopicMap

DAY_1 = datetime(2026, 10, 1, 13, 30, tzinfo=UTC)


def topic(slug: str, day: int, unlock_at: datetime, terms: list[str]) -> Topic:
    return Topic(
        slug=slug,
        day=day,
        title=slug.replace("-", " ").title(),
        audit_brief=f"Brief about {slug}.",
        unlock_at=unlock_at,
        vocabulary=[
            VocabularyTerm(term=t, kind=VocabularyKind.TERM, everyday=t == "bucket")
            for t in terms
        ],
    )


@pytest.fixture
def topics() -> TopicMap:
    return TopicMap(
        plan_id=1,
        baseline_card=["AWS is Amazon's cloud."],
        topics=[
            topic("iam-intro", 1, DAY_1, ["IAM", "principal"]),
            topic("s3-basics", 2, DAY_1 + timedelta(days=1), ["S3", "bucket"]),
            topic("ec2-basics", 3, DAY_1 + timedelta(days=2), ["EC2", "AMI"]),
        ],
    )
