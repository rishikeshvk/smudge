from typing import Annotated, Literal

from pydantic import AwareDatetime, Field

from kindred_contracts.curriculum import Contract


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
