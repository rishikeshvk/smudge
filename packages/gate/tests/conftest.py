import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import httpx2
import pytest

from kindred_contracts import VocabularyKind, VocabularyTerm
from kindred_gate.topics import Topic, TopicMap
from kindred_llm import LLMClient

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


ScriptedLLM = Callable[[list[str]], tuple[LLMClient, list[httpx2.Request]]]


@pytest.fixture
def scripted_llm() -> ScriptedLLM:
    def build(replies: list[str]) -> tuple[LLMClient, list[httpx2.Request]]:
        seen: list[httpx2.Request] = []

        def handler(request: httpx2.Request) -> httpx2.Response:
            seen.append(request)
            return httpx2.Response(
                200,
                json={
                    "id": str(len(seen)),
                    "object": "chat.completion",
                    "created": 0,
                    "model": "scripted",
                    "choices": [
                        {
                            "index": 0,
                            "finish_reason": "stop",
                            "message": {
                                "role": "assistant",
                                "content": replies[len(seen) - 1],
                            },
                        }
                    ],
                },
            )

        client = LLMClient(
            base_url="https://llm.test/v1",
            api_key="sk-test",
            model="scripted",
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
        )
        return client, seen

    return build


@pytest.fixture
def sent_prompt() -> Callable[[httpx2.Request], tuple[str, str]]:
    def read(request: httpx2.Request) -> tuple[str, str]:
        messages = json.loads(request.content)["messages"]
        return messages[0]["content"], messages[1]["content"]

    return read
