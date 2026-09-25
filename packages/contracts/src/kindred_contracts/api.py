from datetime import time
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, SecretStr

from kindred_contracts.cards import Feeling, MessageCard
from kindred_contracts.curriculum import Contract
from kindred_contracts.persona import Mood, Studying
from kindred_contracts.planning import PlanProposal
from kindred_contracts.study import NotebookNote
from kindred_contracts.turn import Speaker, TopicRef, TurnStage


class ClockView(Contract):
    now: AwareDatetime
    real_time: bool
    # None until there is a plan; below 1 before it starts.
    day: int | None


class AdvanceClock(Contract):
    kind: Literal["advance"]
    hours: int = Field(ge=1)


class JumpToDay(Contract):
    """Move to a plan day, keeping the current local time of day."""

    kind: Literal["jump_to_day"]
    day: int = Field(ge=1)


class ResetClock(Contract):
    kind: Literal["real_time"]


ClockChange = Annotated[
    AdvanceClock | JumpToDay | ResetClock, Field(discriminator="kind")
]


class ChatMessage(Contract):
    id: int
    speaker: Speaker
    text: str
    at: AwareDatetime
    # The user's messages move through the turn; the buddy's have no stage.
    stage: TurnStage | None
    # A buddy reply links to its turn for the X-ray view.
    turn_id: int | None
    # Set on the buddy's rituals and on the user's own moments, like joining a session.
    card: MessageCard | None
    # The buddy's emoji on a user message it acknowledged without a reply.
    reaction: str | None


class SendMessage(Contract):
    text: str = Field(min_length=1, max_length=4000)


class MessageStatus(Contract):
    message: ChatMessage
    reply: ChatMessage | None


class BuddyStatus(Contract):
    name: str
    mood: Mood
    # False while the model endpoint fails; messages wait in the queue meanwhile.
    available: bool
    studying: Studying | None


class RoadmapTopic(Contract):
    topic: TopicRef
    unlocks_at: AwareDatetime
    unlocked: bool
    buddy_studied: bool
    user_studied: bool
    # Whether "Pull earlier" can move this topic into the next free study slot.
    can_pull: bool


class RoadmapView(Contract):
    plan_title: str
    # Below 1 before the plan starts.
    day: int
    # The plan's finish day, which a pause moves later.
    last_day: int
    # When the buddy studies each day, in the user's local time.
    study_time: time
    # Days in a row the user has checked in.
    streak: int = Field(ge=0)
    # Topics the buddy is ahead of the user; negative when the user is ahead.
    gap: int
    checked_in_today: bool
    topics: list[RoadmapTopic]


class CheckIn(Contract):
    feeling: Feeling
    fuzzy: str | None = Field(default=None, min_length=1, max_length=280)


class PullTopic(Contract):
    slug: str


class PausePlan(Contract):
    days: int = Field(ge=1, le=7)


class StudyTimeChange(Contract):
    study_time: time


class PushRegistration(Contract):
    token: str = Field(pattern=r"^Expo(nent)?PushToken\[.+\]$")


class SealedDay(Contract):
    """A day whose note isn't written yet: only its day and date, never its content."""

    day: int
    unlocks_at: AwareDatetime


class NotebookView(Contract):
    notes: list[NotebookNote]
    sealed: list[SealedDay]


class OnboardingMessage(Contract):
    text: str = Field(min_length=1, max_length=4000)
    # The device's IANA timezone, so the plan's days follow the user's clock.
    timezone: str


class OnboardingReply(Contract):
    message: ChatMessage
    quick_replies: list[str]
    proposal: PlanProposal | None


class OnboardingEntry(Contract):
    """One message of the onboarding chat, with the plan card a reply offered."""

    message: ChatMessage
    proposal: PlanProposal | None


class AcceptPlan(Contract):
    proposal_message_id: int
    buddy_name: str = Field(min_length=1, max_length=40)


class ModelsPerRole(Contract):
    classifier: str = Field(min_length=1)
    persona: str = Field(min_length=1)
    auditor: str = Field(min_length=1)
    planner: str = Field(min_length=1)
    curator: str = Field(min_length=1)


class LLMSettingsView(Contract):
    base_url: str
    # The key itself never leaves the backend.
    api_key_set: bool
    models: ModelsPerRole


class LLMSettingsUpdate(Contract):
    """Only the fields sent change; the key is write-only."""

    base_url: str | None = Field(default=None, min_length=1)
    api_key: SecretStr | None = Field(default=None, min_length=1)
    models: ModelsPerRole | None = None


class ConnectionCheck(Contract):
    ok: bool
    models: list[str]
    detail: str | None
