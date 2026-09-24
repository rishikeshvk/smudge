from pydantic import AwareDatetime, Field

from kindred_contracts.curriculum import Contract
from kindred_contracts.memory import DaySummary


class ReplyStyle(Contract):
    """How to text back, measured from the user's own recent messages."""

    max_words: int = Field(ge=1)
    # Only when they use emoji themselves.
    emoji: bool


class PersonaContext(Contract):
    """Who the buddy is and where it stands, rebuilt for every turn."""

    buddy_name: str = Field(min_length=1)
    plan_title: str
    # Plan day by the user's local date; below 1 before the plan starts.
    day: int
    # In the user's timezone, so the buddy talks about their morning, not UTC's.
    local_now: AwareDatetime
    # Relationship memory: who the user is, never what the buddy knows.
    facts: list[str]
    recent_days: list[DaySummary]
    # Days in a row the user has checked in.
    streak: int = Field(ge=0)
    # Topics the buddy is ahead of the user; negative when the user is ahead.
    gap: int
    style: ReplyStyle
