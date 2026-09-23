import datetime as dt

from pydantic import Field

from kindred_contracts.curriculum import Contract
from kindred_contracts.turn import ChatTurn, TopicRef


class Course(Contract):
    """A hand-written curriculum the Planner may offer. Its titles are public."""

    slug: str
    title: str
    topics: list[TopicRef]
    study_time: dt.time


class PlannerBrief(Contract):
    today: dt.date
    courses: list[Course] = Field(min_length=1)
    conversation: list[ChatTurn]
    message: str
    feedback: str | None = None


class PlanChoice(Contract):
    """The only parts of a plan the Planner decides; code fills in the rest."""

    curriculum_slug: str
    start_date: dt.date
    study_time: dt.time
    hours_per_day: float = Field(gt=0, le=12)


class PlannerDraft(Contract):
    reply: str = Field(min_length=1)
    # Tappable answers the app shows under the reply.
    quick_replies: list[str] = Field(default=[], max_length=3)
    plan: PlanChoice | None = None


class PlanProposal(Contract):
    curriculum_slug: str
    title: str
    start_date: dt.date
    study_time: dt.time
    hours_per_day: float
    topics: list[TopicRef]
