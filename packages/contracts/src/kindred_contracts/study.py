from pydantic import AwareDatetime, Field, field_validator

from kindred_contracts.curriculum import Contract
from kindred_contracts.knowledge import SortedPoint, SourceExcerpt
from kindred_contracts.turn import TopicRef

MAX_NOTE_WORDS = 400
MAX_SHARE_WORDS = 60


class EarlierNote(Contract):
    topic: TopicRef
    shaky: list[str]


class StudyBrief(Contract):
    """Everything the Curator may see for one night's study, and nothing locked."""

    plan_title: str
    topic: TopicRef
    # What the topic covers, from the curriculum; the topic is unlocked by now.
    focus: str
    baseline_card: list[str]
    earlier: list[EarlierNote]
    sources: list[SourceExcerpt] = Field(min_length=1)
    feedback: str | None = None


class NoteDraft(Contract):
    body: str
    # The seeded gaps: what the buddy honestly didn't get.
    shaky: list[str] = Field(min_length=1, max_length=3)
    sources: list[str] = Field(min_length=1)
    # Tonight's study share: a text to the user about how it went.
    share: str = Field(min_length=1)

    @field_validator("body")
    @classmethod
    def _short_enough_to_embed_whole(cls, body: str) -> str:
        if len(body.split()) > MAX_NOTE_WORDS:
            raise ValueError(f"the note must be at most {MAX_NOTE_WORDS} words")
        return body

    @field_validator("share")
    @classmethod
    def _short_enough_for_a_text(cls, share: str) -> str:
        if len(share.split()) > MAX_SHARE_WORDS:
            raise ValueError(f"the share must be at most {MAX_SHARE_WORDS} words")
        return share


class NotebookNote(Contract):
    note_id: int
    topic: TopicRef
    body: str
    # Every shaky point the note was written with; the sorted ones are also in sorted.
    shaky: list[str]
    sorted: list[SortedPoint]
    sources: list[str]
    written_at: AwareDatetime
