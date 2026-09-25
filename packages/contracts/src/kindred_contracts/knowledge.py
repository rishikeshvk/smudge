from pydantic import Field

from kindred_contracts.curriculum import Contract


class SortedPoint(Contract):
    """A shaky point the user helped the buddy sort out, and what it gets now."""

    shaky: str
    insight: str


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
