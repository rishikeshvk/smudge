import datetime as dt

from pydantic import Field

from kindred_contracts.curriculum import Contract
from kindred_contracts.turn import ChatTurn

MAX_FACTS = 20


class MemoryBrief(Contract):
    """One finished day of chat, plus what the buddy already remembers."""

    buddy_name: str
    day: dt.date
    conversation: list[ChatTurn] = Field(min_length=1)
    facts: list[str]


class MemoryUpdate(Contract):
    summary: str = Field(min_length=1, max_length=600)
    # The whole revised list, so stale facts can be dropped or corrected.
    facts: list[str] = Field(max_length=MAX_FACTS)


class DaySummary(Contract):
    day: dt.date
    summary: str
