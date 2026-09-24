from dataclasses import dataclass
from datetime import time
from enum import StrEnum

from kindred_contracts import (
    AskCard,
    MorningCard,
    NightReviewCard,
    RitualCard,
    StudyShareCard,
    TopicRef,
)

# Templates only ever name the topic titles they're given, and titles are public, so
# they need no runtime audit; test_rituals vets their fixed wording instead.

MORNING_REPLIES = ["Around the same time", "Earlier today", "Not today"]


class RitualKind(StrEnum):
    # In the order a day sends them.
    MORNING = "morning"
    STUDY_SHARE = "study_share"
    ASK = "ask"
    NIGHT_REVIEW = "night_review"


class BuddyNight(StrEnum):
    STUDIED = "studied"
    FAILED = "failed"
    NOT_YET = "not_yet"


@dataclass(frozen=True)
class RitualMessage:
    text: str
    card: RitualCard


def morning(
    day: int, buddy: TopicRef, you: TopicRef | None, study_time: time
) -> RitualMessage:
    at = f"{study_time:%H:%M}"
    openers = [
        f"morning! mine tonight is {buddy.title}, around {at}. you?",
        f"morning. {buddy.title} for me today, sitting down around {at}. when's yours?",
        f"hey, day {day}. I'm on {buddy.title} around {at}. what about you?",
    ]
    text = _variant(openers, day)
    if you is None:
        text += " you've already done every topic, which is great."
    elif you.slug != buddy.slug:
        text += f" you're on {you.title}."
    return RitualMessage(
        text,
        MorningCard(
            kind="morning", day=day, you=you, buddy=buddy, quick_replies=MORNING_REPLIES
        ),
    )


def study_share(
    day: int, topic: TopicRef, share: str, shaky: list[str]
) -> RitualMessage:
    """The Curator's share, audited with its note."""
    return RitualMessage(
        share, StudyShareCard(kind="study_share", day=day, topic=topic, shaky=shaky)
    )


def failed_study_share(day: int, topic: TopicRef) -> RitualMessage:
    text = (
        f"sat down with {topic.title} tonight but couldn't write a note I'd trust, "
        "so that page of my notebook stays empty."
    )
    return RitualMessage(
        text, StudyShareCard(kind="study_share", day=day, topic=topic, shaky=[])
    )


def ask(day: int, note_id: int, topic: TopicRef, shaky: str) -> RitualMessage:
    openers = [
        f"small ask: can you check my note on {topic.title}? I'm still shaky on this:",
        f"could you look at my {topic.title} note sometime? this part didn't click:",
    ]
    return RitualMessage(
        f"{_variant(openers, day)} “{shaky}”",
        AskCard(kind="ask", note_id=note_id, topic=topic),
    )


def night_review(
    day: int,
    buddy: TopicRef,
    night: BuddyNight,
    you_today: TopicRef | None,
    streak: int,
    gap: int,
) -> RitualMessage:
    mine = {
        BuddyNight.STUDIED: f"I finished {buddy.title}.",
        BuddyNight.FAILED: f"{buddy.title} didn't work out for me tonight.",
        BuddyNight.NOT_YET: f"I haven't sat down with {buddy.title} yet.",
    }[night]
    if you_today is None:
        yours = "did you get to yours today?"
    else:
        days = "day" if streak == 1 else "days"
        yours = f"you did {you_today.title}: {streak} {days} in a row for us."
    parts = [_variant(["night check-in.", f"end of day {day}."], day), mine, yours]
    parts.append(_gap(gap))
    return RitualMessage(
        " ".join(parts),
        NightReviewCard(
            kind="night_review",
            day=day,
            streak=streak,
            gap=gap,
            checked_in_today=you_today is not None,
        ),
    )


def _gap(gap: int) -> str:
    topics = "topic" if abs(gap) == 1 else "topics"
    if gap > 0:
        return f"you're {gap} {topics} behind me right now."
    if gap < 0:
        return f"you're {-gap} {topics} ahead of me, nice."
    return "we're level."


def _variant(options: list[str], day: int) -> str:
    return options[day % len(options)]
