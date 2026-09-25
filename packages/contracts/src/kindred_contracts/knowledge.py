from pydantic import AwareDatetime, Field

from kindred_contracts.curriculum import Contract


class SortedPoint(Contract):
    """A shaky point the user helped the buddy sort out, and what it gets now."""

    shaky: str
    insight: str
    sorted_at: AwareDatetime


def still_shaky(shaky: list[str], sorted_points: list[SortedPoint]) -> list[str]:
    """A note's shaky points the user hasn't helped sort out yet."""
    done = {point.shaky for point in sorted_points}
    return [point for point in shaky if point not in done]


class RetrievedNote(Contract):
    note_id: int
    topic_slug: str
    topic_title: str
    day: int = Field(ge=1)
    body: str
    # Every shaky point the note was written with; the sorted ones are also in sorted.
    shaky: list[str]
    sorted: list[SortedPoint]
    distance: float


class SourceExcerpt(Contract):
    """Real material for one topic, as the Curator reads it."""

    url: str
    title: str
    text: str
