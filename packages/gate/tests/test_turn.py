from datetime import datetime

import pytest

from kindred_contracts import (
    AuditVerdict,
    Category,
    ChatTurn,
    Classification,
    Draft,
    DraftRequest,
    RetrievedNote,
    Route,
    TurnTrace,
    Verdict,
)
from kindred_gate.fallback import CRISIS, LOCKED_TOPIC, UNSURE
from kindred_gate.topics import TopicMap
from kindred_gate.turn import TurnComponents, run_turn
from kindred_llm import StructuredOutputError

NOTE = RetrievedNote(
    note_id=1,
    topic_slug="iam-intro",
    topic_title="Iam Intro",
    day=1,
    body="IAM notes",
    shaky=[],
    distance=0.1,
)
PASS = AuditVerdict(verdict=Verdict.PASS, rationale="fine")


def leak(*evidence: str) -> AuditVerdict:
    return AuditVerdict(
        verdict=Verdict.LEAK,
        leaked_topic_slugs=["s3-basics"],
        evidence=list(evidence),
        rationale="explains S3",
    )


class FakeClassifier:
    model = "fake-classifier"

    def __init__(self, result: Classification | None) -> None:
        self._result = result

    async def classify(
        self, message: str, history: list[ChatTurn], topics: TopicMap, session_id: str
    ) -> Classification:
        if self._result is None:
            raise StructuredOutputError("bad json")
        return self._result


class FakeRetriever:
    def __init__(self) -> None:
        self.calls = 0

    async def retrieve(self, message: str, now: datetime) -> list[RetrievedNote]:
        self.calls += 1
        return [NOTE]


class FakeDrafter:
    model = "fake-drafter"

    def __init__(self, *replies: str) -> None:
        self._replies = list(replies)
        self.requests: list[DraftRequest] = []

    async def draft(self, request: DraftRequest, session_id: str) -> Draft:
        self.requests.append(request)
        if not self._replies:
            raise StructuredOutputError("bad json")
        return Draft(reply=self._replies.pop(0))


class FakeAuditor:
    model = "fake-auditor"

    def __init__(self, *verdicts: AuditVerdict | None) -> None:
        self._verdicts = list(verdicts)
        self.drafts: list[str] = []

    async def audit(
        self,
        draft: str,
        message: str,
        history: list[ChatTurn],
        topics: TopicMap,
        now: datetime,
        session_id: str,
    ) -> AuditVerdict:
        self.drafts.append(draft)
        verdict = self._verdicts.pop(0)
        if verdict is None:
            raise StructuredOutputError("bad json")
        return verdict


def about(*slugs: str) -> Classification:
    return Classification(
        category=Category.CURRICULUM, topic_slugs=list(slugs), rationale=""
    )


async def turn(
    topics: TopicMap,
    classification: Classification | None,
    drafter: FakeDrafter,
    auditor: FakeAuditor,
    retriever: FakeRetriever | None = None,
) -> TurnTrace:
    day_1 = topics.topics[0].unlock_at
    return await run_turn(
        "question",
        [],
        now=day_1,
        topics=topics,
        components=TurnComponents(
            classifier=FakeClassifier(classification),
            retriever=retriever or FakeRetriever(),
            drafter=drafter,
            auditor=auditor,
        ),
        session_id="s",
        user_studied=frozenset(t.slug for t in topics.topics),
    )


def assert_audited(trace: TurnTrace) -> None:
    passed = [a.reply for a in trace.attempts if a.audit.verdict is Verdict.PASS]
    assert trace.fell_back or trace.final_reply in passed


@pytest.mark.anyio
async def test_unlocked_question_is_answered_from_notes(topics: TopicMap) -> None:
    retriever = FakeRetriever()
    drafter = FakeDrafter("IAM is about access.")

    trace = await turn(
        topics, about("iam-intro"), drafter, FakeAuditor(PASS), retriever
    )

    assert trace.directive.route is Route.ANSWER
    assert trace.final_reply == "IAM is about access."
    assert not trace.fell_back
    assert retriever.calls == 1
    assert drafter.requests[0].notes == [NOTE]
    assert_audited(trace)


@pytest.mark.anyio
async def test_leaky_draft_is_redrafted_with_feedback(topics: TopicMap) -> None:
    drafter = FakeDrafter("S3 stores objects. IAM is access.", "IAM is access.")
    auditor = FakeAuditor(leak("S3 stores objects.", "not in the draft"), PASS)

    trace = await turn(topics, about("iam-intro"), drafter, auditor)

    assert trace.final_reply == "IAM is access."
    assert len(trace.attempts) == 2
    feedback = drafter.requests[1].feedback
    assert feedback is not None
    assert "S3 Basics" in feedback
    assert "- S3 stores objects." in feedback
    assert "not in the draft" not in feedback
    assert_audited(trace)


@pytest.mark.anyio
async def test_two_leaks_fall_back_to_the_template(topics: TopicMap) -> None:
    trace = await turn(
        topics,
        about("s3-basics"),
        FakeDrafter("S3 stores objects.", "S3 is object storage."),
        FakeAuditor(leak(), leak()),
    )

    assert trace.fell_back
    assert trace.final_reply == LOCKED_TOPIC.format(title="S3 Basics", day=2)
    assert len(trace.attempts) == 2


@pytest.mark.anyio
async def test_invalid_classifier_output_fails_closed(topics: TopicMap) -> None:
    retriever = FakeRetriever()
    auditor = FakeAuditor(PASS)

    trace = await turn(topics, None, FakeDrafter("I'm not sure."), auditor, retriever)

    assert trace.classification.category is Category.UNSURE
    assert trace.directive.route is Route.DEFLECT
    assert retriever.calls == 0
    assert auditor.drafts == ["I'm not sure."]


@pytest.mark.anyio
async def test_invalid_auditor_output_counts_as_a_leak(topics: TopicMap) -> None:
    trace = await turn(
        topics,
        about("iam-intro"),
        FakeDrafter("first", "second"),
        FakeAuditor(None, None),
    )

    assert trace.fell_back
    assert [a.audit.verdict for a in trace.attempts] == [Verdict.LEAK, Verdict.LEAK]


@pytest.mark.anyio
async def test_drafter_failure_falls_back_without_sending_anything(
    topics: TopicMap,
) -> None:
    trace = await turn(topics, about("iam-intro"), FakeDrafter(), FakeAuditor())

    assert trace.fell_back
    assert trace.final_reply == UNSURE
    assert trace.attempts == []


@pytest.mark.anyio
async def test_off_topic_messages_skip_retrieval_but_not_the_audit(
    topics: TopicMap,
) -> None:
    retriever = FakeRetriever()
    auditor = FakeAuditor(PASS)
    off_topic = Classification(category=Category.OFF_TOPIC, rationale="")

    trace = await turn(
        topics, off_topic, FakeDrafter("Go for a walk!"), auditor, retriever
    )

    assert trace.directive.route is Route.GENERAL
    assert retriever.calls == 0
    assert auditor.drafts == ["Go for a walk!"]


@pytest.mark.anyio
async def test_crisis_sends_the_template_without_drafting(topics: TopicMap) -> None:
    drafter = FakeDrafter("study talk")
    crisis = Classification(category=Category.CRISIS, rationale="")

    trace = await turn(topics, crisis, drafter, FakeAuditor())

    assert trace.directive.route is Route.CRISIS
    assert trace.attempts == []
    assert trace.final_reply == CRISIS
