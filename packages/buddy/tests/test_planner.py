from collections.abc import Callable
from datetime import date, time

import httpx2
import pytest

from kindred_buddy.planner import Planner, build_prompt
from kindred_contracts import ChatTurn, Course, PlannerBrief, Speaker, TopicRef
from kindred_llm import LLMClient

ScriptedLLM = Callable[[list[str]], tuple[LLMClient, list[httpx2.Request]]]
SentPrompt = Callable[[httpx2.Request], tuple[str, str]]

BRIEF = PlannerBrief(
    today=date(2026, 9, 23),
    courses=[
        Course(
            slug="aws-2week",
            title="AWS fundamentals in two weeks",
            topics=[
                TopicRef(slug="cloud-basics", title="What AWS is", day=1),
                TopicRef(slug="iam-intro", title="IAM overview", day=2),
            ],
            study_time=time(19),
        )
    ],
    conversation=[ChatTurn(speaker=Speaker.BUDDY, text="what do you want to learn?")],
    message="AWS in 2 weeks, 3 hours a day",
)


def test_prompt_lists_the_courses_and_the_conversation() -> None:
    prompt = build_prompt(BRIEF)

    assert prompt.startswith("Today is Wednesday 23 September 2026.")
    assert "- aws-2week: AWS fundamentals in two weeks, 2 days" in prompt
    assert "usually studied at 19:00" in prompt
    assert "day 2 IAM overview" in prompt
    assert "buddy: what do you want to learn?" in prompt
    assert prompt.endswith("User message:\nAWS in 2 weeks, 3 hours a day")


@pytest.mark.anyio
async def test_the_planner_can_answer_with_a_plan(
    scripted_llm: ScriptedLLM, sent_prompt: SentPrompt
) -> None:
    llm, seen = scripted_llm(
        [
            '{"reply": "an hour a day is easier to keep", '
            '"quick_replies": ["1 hour a day", "Keep 3 hours"], '
            '"plan": {"curriculum_slug": "aws-2week", "start_date": "2026-09-24", '
            '"study_time": "19:00:00", "hours_per_day": 1}}'
        ]
    )

    draft = await Planner(llm).plan(BRIEF, "onboarding-1")

    assert draft.quick_replies == ["1 hour a day", "Keep 3 hours"]
    assert draft.plan is not None
    assert (draft.plan.start_date, draft.plan.hours_per_day) == (date(2026, 9, 24), 1)
    system, _ = sent_prompt(seen[0])
    assert "Only offer the courses listed" in system
