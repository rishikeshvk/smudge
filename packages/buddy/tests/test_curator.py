from collections.abc import Callable

import httpx2
import pytest
from pydantic import ValidationError

from kindred_buddy.curator import SOURCE_BUDGET_CHARS, Curator, build_prompt
from kindred_contracts import (
    EarlierNote,
    NoteDraft,
    SourceExcerpt,
    StudyBrief,
    TopicRef,
)
from kindred_llm import LLMClient

ScriptedLLM = Callable[[list[str]], tuple[LLMClient, list[httpx2.Request]]]
SentPrompt = Callable[[httpx2.Request], tuple[str, str]]

IAM = TopicRef(slug="iam-intro", title="IAM overview", day=3)
POLICIES = TopicRef(slug="iam-policies", title="IAM policies", day=5)


def brief(
    sources: list[SourceExcerpt] | None = None, feedback: str | None = None
) -> StudyBrief:
    return StudyBrief(
        plan_title="AWS fundamentals in two weeks",
        topic=POLICIES,
        focus="Teaches policy documents and how requests are evaluated.",
        baseline_card=["AWS is Amazon's cloud."],
        earlier=[EarlierNote(topic=IAM, shaky=["authN vs authZ"])],
        sources=sources
        or [
            SourceExcerpt(
                url="https://docs.test/policies",
                title="Policies and permissions",
                text="A policy is a JSON document.",
            )
        ],
        feedback=feedback,
    )


def test_prompt_carries_the_topic_its_sources_and_earlier_gaps() -> None:
    prompt = build_prompt(brief())

    assert prompt.startswith("Today: day 5, IAM policies")
    assert "Teaches policy documents" in prompt
    assert "[Policies and permissions](https://docs.test/policies)" in prompt
    assert "A policy is a JSON document." in prompt
    assert "- day 3: IAM overview. Still shaky: authN vs authZ" in prompt
    assert "Feedback" not in prompt


def test_sources_share_the_reading_budget() -> None:
    long = [
        SourceExcerpt(
            url=f"https://docs.test/{n}", title=f"Page {n}", text="x" * 50_000
        )
        for n in range(3)
    ]

    prompt = build_prompt(brief(sources=long))

    assert prompt.count("x") <= SOURCE_BUDGET_CHARS
    assert all(f"Page {n}" in prompt for n in range(3))


def test_redraft_prompt_ends_with_the_feedback() -> None:
    prompt = build_prompt(brief(feedback="Leave out EC2."))

    assert prompt.endswith("Feedback on your last draft:\nLeave out EC2.")


def test_notes_must_be_short_and_have_one_to_three_gaps() -> None:
    with pytest.raises(ValidationError):
        NoteDraft(
            body="word " * 401,
            shaky=["a"],
            sources=["https://docs.test"],
            share="went ok",
        )
    with pytest.raises(ValidationError):
        NoteDraft(body="fine", shaky=[], sources=["https://docs.test"], share="went ok")
    with pytest.raises(ValidationError):
        NoteDraft(
            body="fine",
            shaky=["a", "b", "c", "d"],
            sources=["https://d.test"],
            share="went ok",
        )


@pytest.mark.anyio
async def test_the_note_cites_only_pages_it_was_given(
    scripted_llm: ScriptedLLM, sent_prompt: SentPrompt
) -> None:
    llm, seen = scripted_llm(
        [
            '{"body": "policies are json", "shaky": ["deny beats allow?"], '
            '"sources": ["https://docs.test/policies", "https://elsewhere.test"], '
            '"share": "policies done, deny still confuses me"}'
        ]
    )

    note = await Curator(llm).study(brief(), "study-1")

    assert note.sources == ["https://docs.test/policies"]
    assert note.shaky == ["deny beats allow?"]
    assert note.share == "policies done, deny still confuses me"
    system, _ = sent_prompt(seen[0])
    assert '"AWS fundamentals in two weeks"' in system


@pytest.mark.anyio
async def test_a_note_citing_nothing_given_falls_back_to_its_reading(
    scripted_llm: ScriptedLLM,
) -> None:
    llm, _ = scripted_llm(
        [
            '{"body": "b", "shaky": ["s"], "sources": ["https://elsewhere.test"], '
            '"share": "done"}'
        ]
    )

    note = await Curator(llm).study(brief(), "study-1")

    assert note.sources == ["https://docs.test/policies"]
