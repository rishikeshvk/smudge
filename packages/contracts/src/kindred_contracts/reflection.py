from pydantic import Field, field_validator

from kindred_contracts.curriculum import Contract
from kindred_contracts.knowledge import SourceExcerpt
from kindred_contracts.turn import ChatTurn, TopicRef

MAX_INSIGHT_WORDS = 40


class ReflectionBrief(Contract):
    """A topic's open shaky points, what the user said about it in a day, and the
    topic's own sources to check it against. Nothing locked."""

    plan_title: str
    topic: TopicRef
    open_shaky: list[str] = Field(min_length=1)
    exchanges: list[ChatTurn] = Field(min_length=1)
    sources: list[SourceExcerpt] = Field(min_length=1)


class ReflectedPoint(Contract):
    shaky: str
    sorted: bool
    # What the buddy understands now, in its own words; empty unless sorted.
    insight: str = ""

    @field_validator("insight")
    @classmethod
    def _short(cls, insight: str) -> str:
        if len(insight.split()) > MAX_INSIGHT_WORDS:
            raise ValueError(f"the insight must be at most {MAX_INSIGHT_WORDS} words")
        return insight


class Reflection(Contract):
    points: list[ReflectedPoint]
