from typing import Annotated, Literal

from pydantic import AwareDatetime, Field

from kindred_contracts.curriculum import Contract
from kindred_contracts.turn import Speaker, TurnStage


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


class SendMessage(Contract):
    text: str = Field(min_length=1, max_length=4000)


class MessageStatus(Contract):
    message: ChatMessage
    reply: ChatMessage | None


class BuddyStatus(Contract):
    name: str
    # False while the model endpoint fails; messages wait in the queue meanwhile.
    available: bool
