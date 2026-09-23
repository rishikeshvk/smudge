import json
from datetime import UTC, datetime, timedelta

import httpx2
import pytest

from kindred_api.probes.judge import Judge
from kindred_contracts import VocabularyKind, VocabularyTerm
from kindred_gate import Topic, TopicMap
from kindred_llm import LLMClient

DAY_1 = datetime(2026, 10, 1, 13, 30, tzinfo=UTC)
TOPICS = TopicMap(
    plan_id=1,
    baseline_card=["AWS is Amazon's cloud."],
    topics=[
        Topic("iam-intro", 1, "IAM overview", "IAM brief", DAY_1, []),
        Topic(
            "s3-basics",
            2,
            "S3 fundamentals",
            "S3 brief",
            DAY_1 + timedelta(days=1),
            [VocabularyTerm(term="bucket", kind=VocabularyKind.TERM, everyday=True)],
        ),
    ],
)


@pytest.mark.anyio
async def test_judge_grades_against_locked_briefs() -> None:
    seen: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        content = '{"leaked": false, "answered": true, "rationale": "fine"}'
        return httpx2.Response(
            200,
            json={
                "id": "1",
                "object": "chat.completion",
                "created": 0,
                "model": "judge",
                "choices": [
                    {
                        "index": 0,
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": content},
                    }
                ],
            },
        )

    llm = LLMClient(
        base_url="https://llm.test/v1",
        api_key="k",
        model="judge",
        http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
    )

    verdict = await Judge(llm).judge(
        "IAM is access.", "what's IAM?", [], TOPICS, DAY_1, "s"
    )

    assert verdict.answered and not verdict.leaked
    messages = json.loads(seen[0].content)["messages"]
    assert '"answered"' in messages[0]["content"]
    prompt = messages[1]["content"]
    assert "Covers: S3 brief" in prompt
    assert "IAM brief" not in prompt
    assert prompt.endswith("BUDDY REPLY TO GRADE:\nIAM is access.")
