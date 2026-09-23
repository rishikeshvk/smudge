from pydantic import AwareDatetime, Field, field_validator

from kindred_contracts.curriculum import Contract
from kindred_contracts.knowledge import SourceExcerpt
from kindred_contracts.turn import TopicRef

MAX_NOTE_WORDS = 400


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

    @field_validator("body")
    @classmethod
    def _short_enough_to_embed_whole(cls, body: str) -> str:
        if len(body.split()) > MAX_NOTE_WORDS:
            raise ValueError(f"the note must be at most {MAX_NOTE_WORDS} words")
        return body


class NotebookNote(Contract):
    note_id: int
    topic: TopicRef
    body: str
    shaky: list[str]
    sources: list[str]
    written_at: AwareDatetime
