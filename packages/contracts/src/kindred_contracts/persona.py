from pydantic import AwareDatetime, Field

from kindred_contracts.curriculum import Contract


class PersonaContext(Contract):
    """Who the buddy is and where it stands, rebuilt for every turn."""

    buddy_name: str = Field(min_length=1)
    plan_title: str
    # Plan day by the user's local date; below 1 before the plan starts.
    day: int
    # In the user's timezone, so the buddy talks about their morning, not UTC's.
    local_now: AwareDatetime
