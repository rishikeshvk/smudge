from datetime import time
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class Contract(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        # Serialized output always carries defaulted fields; say so in the schema.
        json_schema_serialization_defaults_required=True,
    )


class VocabularyKind(StrEnum):
    TERM = "term"
    SYNONYM = "synonym"
    ABBREVIATION = "abbreviation"
    API_NAME = "api_name"


class VocabularyTerm(Contract):
    term: str = Field(min_length=1)
    kind: VocabularyKind
    # Also an ordinary English word (bucket, role), so its mere presence says nothing.
    everyday: bool = False


class StudyNote(Contract):
    body: str = Field(min_length=1)
    shaky: list[str] = Field(min_length=1)
    sources: list[HttpUrl] = Field(min_length=1)


class TopicNode(Contract):
    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    day: int = Field(ge=1)
    title: str = Field(min_length=1)
    prerequisites: list[str] = []
    audit_brief: str = Field(min_length=1)
    vocabulary: list[VocabularyTerm] = Field(min_length=1)
    notes: list[StudyNote] = Field(min_length=1)


class Curriculum(Contract):
    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    title: str = Field(min_length=1)
    study_time: time
    baseline_card: list[str] = Field(min_length=1)
    nodes: list[TopicNode] = Field(min_length=1)

    @model_validator(mode="after")
    def check_topic_graph(self) -> Self:
        days = sorted(node.day for node in self.nodes)
        if days != list(range(1, len(self.nodes) + 1)):
            raise ValueError("node days must run 1..n with no gaps or repeats")

        day_by_slug = {node.slug: node.day for node in self.nodes}
        if len(day_by_slug) != len(self.nodes):
            raise ValueError("node slugs must be unique")

        for node in self.nodes:
            for prerequisite in node.prerequisites:
                if prerequisite not in day_by_slug:
                    raise ValueError(
                        f"{node.slug}: unknown prerequisite {prerequisite}"
                    )
                if day_by_slug[prerequisite] >= node.day:
                    raise ValueError(
                        f"{node.slug}: {prerequisite} must come on an earlier day"
                    )
        return self
