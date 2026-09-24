from datetime import date, datetime, time, timedelta

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    MetaData,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EMBEDDING_DIMENSIONS = 1024


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )
    type_annotation_map = {datetime: DateTime(timezone=True), str: Text}


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    timezone: Mapped[str]


# One persona per user, kept across every goal they take on.
class Buddy(Base):
    __tablename__ = "buddies"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    name: Mapped[str]


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    curriculum_slug: Mapped[str]
    title: Mapped[str]
    start_date: Mapped[date]
    study_time: Mapped[time]
    baseline_card: Mapped[list[str]] = mapped_column(JSONB)


class TopicNode(Base):
    __tablename__ = "topic_nodes"
    __table_args__ = (
        UniqueConstraint("plan_id", "slug"),
        # Checked at commit, so replanning can shift a run of days in one go.
        UniqueConstraint("plan_id", "day", deferrable=True, initially="DEFERRED"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    slug: Mapped[str]
    day: Mapped[int]
    title: Mapped[str]
    audit_brief: Mapped[str]
    unlock_at: Mapped[datetime]


class TopicPrerequisite(Base):
    __tablename__ = "topic_prerequisites"
    __table_args__ = (CheckConstraint("node_id <> prerequisite_id", name="not_self"),)

    node_id: Mapped[int] = mapped_column(ForeignKey("topic_nodes.id"), primary_key=True)
    prerequisite_id: Mapped[int] = mapped_column(
        ForeignKey("topic_nodes.id"), primary_key=True
    )


class TopicVocabulary(Base):
    __tablename__ = "topic_vocabulary"

    id: Mapped[int] = mapped_column(primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("topic_nodes.id"), index=True)
    term: Mapped[str]
    kind: Mapped[str]
    everyday: Mapped[bool]


# What the buddy knows; append-only, enforced by a trigger in the migration.
class LedgerNote(Base):
    __tablename__ = "ledger_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    node_id: Mapped[int] = mapped_column(
        ForeignKey("topic_nodes.id", ondelete="RESTRICT"), index=True
    )
    body: Mapped[str]
    shaky: Mapped[list[str]] = mapped_column(JSONB)
    sources: Mapped[list[str]] = mapped_column(ARRAY(Text))
    written_at: Mapped[datetime]


# Real material the buddy studies from, gated by its topic's unlock like the notes.
class SourceDocument(Base):
    __tablename__ = "source_documents"
    __table_args__ = (UniqueConstraint("node_id", "url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("topic_nodes.id"), index=True)
    url: Mapped[str]
    title: Mapped[str]
    text: Mapped[str]
    fetched_at: Mapped[datetime]


# Kept apart from the ledger so embedding, or re-embedding with a new model,
# never has to update an append-only row.
class NoteEmbedding(Base):
    __tablename__ = "note_embeddings"

    note_id: Mapped[int] = mapped_column(
        ForeignKey("ledger_notes.id", ondelete="RESTRICT"), primary_key=True
    )
    model: Mapped[str] = mapped_column(primary_key=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))


# Every pipeline turn, for the X-ray view and eval runs.
class Turn(Base):
    __tablename__ = "turns"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), index=True)
    session_id: Mapped[str]
    probe_run_id: Mapped[str | None] = mapped_column(index=True)
    at: Mapped[datetime]
    message: Mapped[str]
    route: Mapped[str]
    fell_back: Mapped[bool]
    final_reply: Mapped[str]
    trace: Mapped[dict[str, object]] = mapped_column(JSONB)


# Dev-only time travel: how far Kindred's clock runs ahead of real time.
class DevClock(Base):
    __tablename__ = "dev_clock"
    __table_args__ = (CheckConstraint("id = 1", name="single_row"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    offset: Mapped[timedelta]


# The chat thread belongs to the user, since the buddy lasts across goals.
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # "chat" once a plan exists; "onboarding" while planning it together.
    thread: Mapped[str] = mapped_column(server_default="chat")
    speaker: Mapped[str]
    text: Mapped[str]
    at: Mapped[datetime]
    # A Planner reply's plan proposal, kept so the user can accept it later.
    proposal: Mapped[dict[str, object] | None] = mapped_column(JSONB)
    # Set on user messages only: where each one is on its way to a reply.
    stage: Mapped[str | None] = mapped_column(index=True)
    reply_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("messages.id"), unique=True
    )
    turn_id: Mapped[int | None] = mapped_column(ForeignKey("turns.id"))
    # A ritual's card: what the app draws around the text.
    card: Mapped[dict[str, object] | None] = mapped_column(JSONB)


# The user saying "I studied today"; one per topic, in plan order.
class StudyCheckin(Base):
    __tablename__ = "study_checkins"

    id: Mapped[int] = mapped_column(primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("topic_nodes.id"), unique=True)
    at: Mapped[datetime]


# One night's study per topic: the note it wrote, or why it wrote nothing.
class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("topic_nodes.id"), unique=True)
    status: Mapped[str]
    at: Mapped[datetime]
    note_id: Mapped[int | None] = mapped_column(ForeignKey("ledger_notes.id"))
    # The written note's study share, audited with it; the Director sends it.
    share: Mapped[str | None]
    # Every draft and its audit, for debugging what the Curator tried.
    attempts: Mapped[list[dict[str, object]]] = mapped_column(JSONB)


# One ritual per plan day and kind, so a tick never sends one twice.
class Ritual(Base):
    __tablename__ = "rituals"
    __table_args__ = (UniqueConstraint("plan_id", "day", "kind"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    day: Mapped[int]
    kind: Mapped[str]
    message_id: Mapped[int] = mapped_column(ForeignKey("messages.id"))
    # A small ask's shaky point, so none is asked twice.
    note_id: Mapped[int | None] = mapped_column(ForeignKey("ledger_notes.id"))
    shaky: Mapped[str | None]


# A phone that gets the buddy's rituals as push notifications, via Expo.
class PushToken(Base):
    __tablename__ = "push_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(unique=True)
    registered_at: Mapped[datetime]


# Who the user is to the buddy: one snapshot per finished day, kept apart from the
# ledger of what it knows. The latest snapshot is the current memory.
class RelationshipMemory(Base):
    __tablename__ = "relationship_memory"
    __table_args__ = (UniqueConstraint("user_id", "for_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    for_date: Mapped[date]
    summary: Mapped[str]
    facts: Mapped[list[str]] = mapped_column(JSONB)
    written_at: Mapped[datetime]


# Bring-your-own-key settings saved from the app; each set field overrides .env.
class LLMSettings(Base):
    __tablename__ = "llm_settings"
    __table_args__ = (CheckConstraint("id = 1", name="single_row"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    base_url: Mapped[str | None]
    api_key: Mapped[str | None]
    models: Mapped[dict[str, str] | None] = mapped_column(JSONB)
