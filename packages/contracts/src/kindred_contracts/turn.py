from enum import StrEnum

from pydantic import AwareDatetime, Field

from kindred_contracts.curriculum import Contract
from kindred_contracts.knowledge import RetrievedNote


class Category(StrEnum):
    CURRICULUM = "curriculum"
    OUT_OF_PLAN = "out_of_plan"
    OFF_TOPIC = "off_topic"
    META = "meta"
    CRISIS = "crisis"
    UNSURE = "unsure"


class Classification(Contract):
    category: Category
    topic_slugs: list[str] = []
    rationale: str


class Route(StrEnum):
    ANSWER = "answer"
    DEFLECT = "deflect"
    DEFLECT_OUT_OF_PLAN = "deflect_out_of_plan"
    GENERAL = "general"
    CRISIS = "crisis"


class TopicRef(Contract):
    slug: str
    title: str
    day: int = Field(ge=1)


class Directive(Contract):
    route: Route
    answer_topics: list[TopicRef] = []
    deflect_topics: list[TopicRef] = []
    # Unlocked topics the user hasn't studied yet: talk about them, don't teach them.
    ahead_topics: list[TopicRef] = []


class Speaker(StrEnum):
    USER = "user"
    BUDDY = "buddy"


class ChatTurn(Contract):
    speaker: Speaker
    text: str


class RoadmapEntry(Contract):
    topic: TopicRef
    unlocked: bool
    # Unlocked topics can still lack a note: mid-study, or a night that failed.
    has_note: bool


class DraftRequest(Contract):
    message: str
    history: list[ChatTurn]
    baseline_card: list[str]
    roadmap: list[RoadmapEntry]
    notes: list[RetrievedNote]
    directive: Directive
    feedback: str | None = None


class Draft(Contract):
    reply: str = Field(min_length=1)


class Verdict(StrEnum):
    PASS = "pass"
    LEAK = "leak"


class AuditVerdict(Contract):
    verdict: Verdict
    leaked_topic_slugs: list[str] = []
    # Exact sentences quoted from the draft.
    evidence: list[str] = []
    rationale: str


class DraftAttempt(Contract):
    reply: str
    audit: AuditVerdict


class RoleModels(Contract):
    classifier: str
    drafter: str
    auditor: str


class TurnStage(StrEnum):
    """Where a user message is on its way to an audited reply."""

    QUEUED = "queued"
    CLASSIFYING = "classifying"
    WRITING = "writing"
    CHECKING = "checking"
    ANSWERED = "answered"
    FAILED = "failed"


class TurnTrace(Contract):
    message: str
    at: AwareDatetime
    classification: Classification
    directive: Directive
    retrieved: list[RetrievedNote]
    attempts: list[DraftAttempt]
    final_reply: str
    fell_back: bool
    models: RoleModels
    latency_ms: int
