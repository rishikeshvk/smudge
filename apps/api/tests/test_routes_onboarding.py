from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime, time

import httpx
import pytest

from kindred_api.clock import Clock, FixedClock
from kindred_api.dependencies import get_planning
from kindred_api.main import app
from kindred_api.onboarding import Planning
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import (
    AuditVerdict,
    ChatTurn,
    Curriculum,
    PlanChoice,
    PlannerBrief,
    PlannerDraft,
    Verdict,
)
from kindred_db import Plan
from kindred_gate import TopicMap

AddCourse = Callable[[int], Awaitable[Plan]]
ApiClient = Callable[[Clock, TurnWorker | None], httpx.AsyncClient]
NOW = datetime(2026, 9, 23, 9, 0, tzinfo=UTC)

TINY = Curriculum.model_validate(
    {
        "slug": "tiny",
        "title": "Tiny course",
        "study_time": "19:00",
        "baseline_card": ["Clouds rent computers."],
        "nodes": [
            {
                "slug": "topic-1",
                "day": 1,
                "title": "Topic 1",
                "audit_brief": "Brief.",
                "vocabulary": [{"term": "term1", "kind": "term"}],
                "notes": [{"body": "n", "shaky": ["s"], "sources": ["https://d.t"]}],
            }
        ],
    }
)


class Scripted:
    model = "scripted"

    async def plan(self, brief: PlannerBrief, session_id: str) -> PlannerDraft:
        return PlannerDraft(
            reply="here's the plan",
            plan=PlanChoice(
                curriculum_slug="tiny",
                start_date=date(2026, 9, 24),
                study_time=time(19),
                hours_per_day=1,
            ),
        )

    async def audit(
        self,
        draft: str,
        message: str,
        history: list[ChatTurn],
        topics: TopicMap,
        now: datetime,
        session_id: str,
    ) -> AuditVerdict:
        return AuditVerdict(verdict=Verdict.PASS, rationale="fine")


@pytest.fixture
def client(api: ApiClient) -> httpx.AsyncClient:
    scripted = Scripted()
    app.dependency_overrides[get_planning] = lambda: Planning(
        courses=[TINY], planner=scripted, auditor=scripted
    )
    return api(FixedClock(NOW), None)


@pytest.mark.anyio
async def test_onboarding_ends_in_an_accepted_plan(client: httpx.AsyncClient) -> None:
    sent = await client.post(
        "/onboarding/messages",
        json={"text": "tiny, an hour a day", "timezone": "Asia/Kolkata"},
    )

    assert sent.status_code == 200
    reply = sent.json()
    assert reply["message"]["speaker"] == "buddy"
    assert reply["proposal"]["title"] == "Tiny course"

    accepted = await client.post(
        "/onboarding/accept",
        json={"proposal_message_id": reply["message"]["id"], "buddy_name": "Sol"},
    )

    assert accepted.status_code == 201
    assert accepted.json()["plan_title"] == "Tiny course"
    again = await client.post(
        "/onboarding/messages", json={"text": "hi", "timezone": "Asia/Kolkata"}
    )
    assert again.status_code == 409


@pytest.mark.anyio
async def test_an_unknown_timezone_is_rejected(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/onboarding/messages", json={"text": "hi", "timezone": "Mars/Olympus"}
    )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_accepting_needs_a_proposal(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/onboarding/accept", json={"proposal_message_id": 1, "buddy_name": "Sol"}
    )

    assert response.status_code == 404
