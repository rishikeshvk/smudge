from datetime import date, datetime, time

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
        UniqueConstraint("plan_id", "day"),
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
