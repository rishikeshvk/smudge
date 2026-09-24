from typing import Annotated, Literal

from pydantic import Field

from kindred_contracts.curriculum import Contract
from kindred_contracts.turn import TopicRef


class MorningCard(Contract):
    kind: Literal["morning"]
    day: int
    # None once the user has checked in on every topic.
    you: TopicRef | None
    buddy: TopicRef
    quick_replies: list[str]


class StudyShareCard(Contract):
    kind: Literal["study_share"]
    day: int
    topic: TopicRef
    # Empty when the buddy couldn't write a note it trusts.
    shaky: list[str]


class AskCard(Contract):
    kind: Literal["ask"]
    note_id: int
    topic: TopicRef


class NightReviewCard(Contract):
    kind: Literal["night_review"]
    day: int
    streak: int = Field(ge=0)
    gap: int
    # The card offers "I studied today" only until the user has.
    checked_in_today: bool


RitualCard = Annotated[
    MorningCard | StudyShareCard | AskCard | NightReviewCard,
    Field(discriminator="kind"),
]
