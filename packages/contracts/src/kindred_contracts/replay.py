from pydantic import Field

from kindred_contracts.api import ChatMessage
from kindred_contracts.curriculum import Contract
from kindred_contracts.study import NotebookNote
from kindred_contracts.turn import TopicRef, TurnTrace


class ReplayMessage(Contract):
    message: ChatMessage
    # The audited turn behind a buddy reply, shown in the X-ray drawer.
    trace: TurnTrace | None


class ReplayDay(Contract):
    # Day 0 is the evening the plan was made, before day one starts.
    day: int = Field(ge=0)
    topic: TopicRef | None
    messages: list[ReplayMessage]


class Replay(Contract):
    """A recorded run, exported for the landing page to play back."""

    buddy_name: str
    plan_title: str
    onboarding: list[ChatMessage]
    days: list[ReplayDay]
    notes: list[NotebookNote]
