from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field

from kindred_contracts.curriculum import Contract
from kindred_contracts.rituals import (
    AskCard,
    MorningCard,
    NightReviewCard,
    StudyShareCard,
)
from kindred_contracts.turn import TopicRef


class Feeling(StrEnum):
    SOLID = "solid"
    OKAY = "okay"
    ROUGH = "rough"


class CheckinCard(Contract):
    """The user's "I studied today", with how it went, so both can compare notes."""

    kind: Literal["checkin"]
    topic: TopicRef
    feeling: Feeling
    fuzzy: str | None


class StudyTogetherCard(Contract):
    """The user joining the buddy's study session: both lamps on until it ends."""

    kind: Literal["study_together"]
    topic: TopicRef
    until: AwareDatetime


# What the app draws around a message: the buddy's rituals, or the user's own moments.
MessageCard = Annotated[
    MorningCard
    | StudyShareCard
    | AskCard
    | NightReviewCard
    | StudyTogetherCard
    | CheckinCard,
    Field(discriminator="kind"),
]
