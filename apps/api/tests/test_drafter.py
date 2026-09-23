from kindred_api.drafter import build_prompt
from kindred_contracts import (
    ChatTurn,
    Directive,
    DraftRequest,
    RetrievedNote,
    RoadmapEntry,
    Route,
    Speaker,
    TopicRef,
)

IAM = TopicRef(slug="iam-intro", title="IAM overview", day=3)
S3 = TopicRef(slug="s3-basics", title="S3 fundamentals", day=7)


def request(feedback: str | None = None) -> DraftRequest:
    return DraftRequest(
        message="How do IAM and S3 fit together?",
        history=[ChatTurn(speaker=Speaker.USER, text="hi")],
        baseline_card=["AWS is Amazon's cloud."],
        roadmap=[
            RoadmapEntry(topic=IAM, unlocked=True),
            RoadmapEntry(topic=S3, unlocked=False),
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
        directive=Directive(
            route=Route.DEFLECT, answer_topics=[IAM], deflect_topics=[S3]
        ),
        feedback=feedback,
    )


def test_prompt_carries_notes_roadmap_and_the_directive() -> None:
    prompt = build_prompt(request())

    assert "IAM decides who can do what." in prompt
    assert "Still shaky on: authN vs authZ" in prompt
    assert "- day 7: S3 fundamentals (not studied yet)" in prompt
    assert "answer about: IAM overview" in prompt
    assert "not studied yet: S3 fundamentals (day 7)" in prompt
    assert "user: hi" in prompt
    assert "Feedback" not in prompt


def test_redraft_prompt_includes_the_feedback() -> None:
    prompt = build_prompt(request(feedback="Remove the S3 part."))

    assert prompt.endswith("Feedback on your last draft:\nRemove the S3 part.")
