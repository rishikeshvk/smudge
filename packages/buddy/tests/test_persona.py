from collections.abc import Callable
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx2
import pytest

from kindred_buddy.persona import Persona, build_prompt
from kindred_contracts import (
    ChatTurn,
    DaySummary,
    Directive,
    DraftRequest,
    Mood,
    MoodKind,
    PersonaContext,
    ReplyStyle,
    RetrievedNote,
    RoadmapEntry,
    Route,
    Speaker,
    TopicRef,
)
from kindred_llm import LLMClient

ScriptedLLM = Callable[[list[str]], tuple[LLMClient, list[httpx2.Request]]]
SentPrompt = Callable[[httpx2.Request], tuple[str, str]]

IAM = TopicRef(slug="iam-intro", title="IAM overview", day=3)
POLICIES = TopicRef(slug="iam-policies", title="IAM policies", day=5)
S3 = TopicRef(slug="s3-basics", title="S3 fundamentals", day=7)

CONTEXT = PersonaContext(
    buddy_name="Juno",
    plan_title="AWS fundamentals in two weeks",
    day=5,
    local_now=datetime(2026, 10, 5, 21, 15, tzinfo=ZoneInfo("Asia/Kolkata")),
    facts=["Studies after work."],
    recent_days=[DaySummary(day=date(2026, 10, 4), summary="they were tired.")],
    streak=3,
    gap=1,
    style=ReplyStyle(max_words=15, emoji=False),
    mood=Mood(kind=MoodKind.STEADY, reason=None),
)


def request(directive: Directive, feedback: str | None = None) -> DraftRequest:
    return DraftRequest(
        message="How do IAM and S3 fit together?",
        history=[ChatTurn(speaker=Speaker.USER, text="hi")],
        baseline_card=["AWS is Amazon's cloud."],
        roadmap=[
            RoadmapEntry(topic=IAM, unlocked=True, has_note=True),
            RoadmapEntry(topic=POLICIES, unlocked=True, has_note=False),
            RoadmapEntry(topic=S3, unlocked=False, has_note=False),
        ],
        notes=[
            RetrievedNote(
                note_id=1,
                topic_slug="iam-intro",
                topic_title="IAM overview",
                day=3,
                body="IAM decides who can do what.",
                shaky=["authN vs authZ"],
                distance=0.2,
            )
        ],
        directive=directive,
        feedback=feedback,
    )


DEFLECT = Directive(route=Route.DEFLECT, answer_topics=[IAM], deflect_topics=[S3])


def test_prompt_carries_notes_roadmap_and_the_directive() -> None:
    prompt = build_prompt(request(DEFLECT), CONTEXT)

    assert "IAM decides who can do what." in prompt
    assert "Still shaky on: authN vs authZ" in prompt
    assert "- day 3: IAM overview (studied)" in prompt
    assert "- day 7: S3 fundamentals (not studied yet)" in prompt
    assert "answer about: IAM overview" in prompt
    assert "not studied yet: S3 fundamentals (day 7)" in prompt
    assert "user: hi" in prompt
    assert "Feedback" not in prompt


def test_prompt_never_calls_an_unlocked_topic_without_a_note_studied() -> None:
    prompt = build_prompt(request(DEFLECT), CONTEXT)

    assert "- day 5: IAM policies (unlocked, but you have no note for it yet)" in prompt


def test_prompt_places_the_buddy_in_the_users_day() -> None:
    prompt = build_prompt(request(DEFLECT), CONTEXT)

    assert prompt.startswith("Now: Monday 21:15, day 5 of the plan.")


def test_prompt_names_topics_the_buddy_is_ahead_on() -> None:
    directive = Directive(
        route=Route.ANSWER, answer_topics=[IAM, POLICIES], ahead_topics=[POLICIES]
    )

    prompt = build_prompt(request(directive), CONTEXT)

    assert "answer about: IAM overview, IAM policies" in prompt
    assert "ahead of the user on: IAM policies" in prompt


def test_redraft_prompt_includes_the_feedback() -> None:
    prompt = build_prompt(request(DEFLECT, feedback="Remove the S3 part."), CONTEXT)

    assert prompt.endswith("Feedback on your last draft:\nRemove the S3 part.")


@pytest.mark.anyio
async def test_persona_speaks_as_the_named_buddy(
    scripted_llm: ScriptedLLM, sent_prompt: SentPrompt
) -> None:
    llm, seen = scripted_llm(['{"reply": "iam clicked for me, s3 is day 7 though"}'])

    draft = await Persona(llm, CONTEXT).draft(request(DEFLECT), "thread-1:drafter")

    assert draft.reply == "iam clicked for me, s3 is day 7 though"
    system, _ = sent_prompt(seen[0])
    assert system.startswith("You are Juno, an AI study buddy.")
    assert '"AWS fundamentals in two weeks"' in system
    assert seen[0].headers["x-opencode-session"] == "thread-1:drafter"


def test_prompt_carries_relationship_memory() -> None:
    prompt = build_prompt(request(DEFLECT), CONTEXT)

    assert "What you remember about them:\n- Studies after work." in prompt
    assert "Recent days together:\n- Sunday: they were tired." in prompt


def test_prompt_says_where_both_learners_stand() -> None:
    prompt = build_prompt(request(DEFLECT), CONTEXT)

    assert (
        "Where you both are: you're 1 topic ahead of them. "
        "They've studied 3 days in a row." in prompt
    )


def test_prompt_says_when_the_user_is_ahead() -> None:
    context = CONTEXT.model_copy(update={"gap": -2, "streak": 1})

    prompt = build_prompt(request(DEFLECT), context)

    assert "they're 2 topics ahead of you. They've studied 1 day in a row." in prompt


def test_prompt_gives_a_reply_budget_matched_to_the_user() -> None:
    prompt = build_prompt(request(DEFLECT), CONTEXT)

    assert "Reply budget: at most 15 words; no emoji, they don't use them." in prompt


def test_emoji_are_allowed_only_when_the_user_uses_them() -> None:
    context = CONTEXT.model_copy(update={"style": ReplyStyle(max_words=30, emoji=True)})

    prompt = build_prompt(request(DEFLECT), context)

    assert "Reply budget: at most 30 words; an emoji is fine." in prompt


def test_a_steady_mood_is_just_named() -> None:
    assert "Your mood: steady." in build_prompt(request(DEFLECT), CONTEXT)


def test_a_mood_with_a_reason_colours_the_tone_without_being_announced() -> None:
    context = CONTEXT.model_copy(
        update={"mood": Mood(kind=MoodKind.FRIED, reason="IAM overview was a lot")}
    )

    prompt = build_prompt(request(DEFLECT), context)

    assert "Your mood: fried, since IAM overview was a lot." in prompt
    assert "don't announce it" in prompt
