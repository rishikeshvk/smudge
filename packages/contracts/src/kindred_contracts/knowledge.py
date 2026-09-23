from pydantic import Field

from kindred_contracts.curriculum import Contract


class RetrievedNote(Contract):
    note_id: int
    topic_slug: str
    topic_title: str
    day: int = Field(ge=1)
    body: str
    shaky: list[str]
    distance: float


class SourceExcerpt(Contract):
    """Real material for one topic, as the Curator reads it."""

    url: str
    title: str
    text: str
