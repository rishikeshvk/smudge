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
class Retried:
    """An earlier topic the buddy had another go at overnight, after a failed night."""

    topic: TopicRef
    worked: bool


@dataclass(frozen=True)
class RitualMessage:
    text: str
    card: RitualCard


def morning(
    day: int,
    buddy: TopicRef,
    you: TopicRef | None,
    study_time: time,
    retried: Retried | None = None,
    thanks: TopicRef | None = None,
) -> RitualMessage:
    at = f"{study_time:%H:%M}"
    mine = _variant(
        [
            f"morning. {buddy.title} for me today, around {at}.",
            f"morning. I'm on {buddy.title} later, sitting down around {at}.",
            f"day {day}. mine's {buddy.title}, around {at}.",
            f"hey. {buddy.title} today for me, {at}-ish.",
        ],
        day,
    )
    if you is None:
        yours = "you've done every topic already, so it's just me today."
    else:
        where = (
            "same one for you." if you.slug == buddy.slug else f"yours is {you.title}."
        )
        when = _variant(
            ["when are you on it?", "you around then too?", "when's yours?"], day
        )
        yours = f"{where} {when}"
    parts = [mine]
    if retried is not None:
        parts.append(_retry(retried))
    if thanks is not None:
        parts.append(
            f"thought about what you said on {thanks.title}, and that bit makes sense "
            "to me now. thanks."
        )
    parts.append(yours)
    return RitualMessage(
        " ".join(parts),
        MorningCard(
            kind="morning", day=day, you=you, buddy=buddy, quick_replies=MORNING_REPLIES
        ),
    )


def _retry(retried: Retried) -> str:
    if retried.worked:
        return (
            f"had another go at {retried.topic.title} overnight and it worked, "
            "the note's in my notebook."
        )
    return (
        f"had another go at {retried.topic.title} overnight, still no note I'd trust, "
        "so I'm leaving that one."
    )


def study_share(
    day: int, topic: TopicRef, share: str, shaky: list[str]
) -> RitualMessage:
    """The Curator's share, audited with its note."""
    return RitualMessage(
        share, StudyShareCard(kind="study_share", day=day, topic=topic, shaky=shaky)
    )


def failed_study_share(day: int, topic: TopicRef) -> RitualMessage:
    text = _variant(
        [
            f"sat down with {topic.title} tonight but couldn't write a note I'd trust. "
            "I'll have another go overnight.",
            f"{topic.title} didn't come together for me tonight, no note I'd trust. "
            "I'll give it another go overnight.",
        ],
        day,
    )
    return RitualMessage(
        text, StudyShareCard(kind="study_share", day=day, topic=topic, shaky=[])
    )


def ask(day: int, note_id: int, topic: TopicRef, shaky: str) -> RitualMessage:
    openers = [
        f"small ask: could you look at my note on {topic.title} sometime? "
        "this bit didn't click:",
        f"when you get a sec, can you check my {topic.title} note? "
        "still stuck on this:",
        f"could you sanity-check my note on {topic.title}? I don't get this part:",
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
    opener = _variant(
        ["night check-in.", f"end of day {day}.", f"wrapping up day {day}."], day
    )
    mine = {
        BuddyNight.STUDIED: _variant(
            [f"{buddy.title} is done on my side.", f"I got through {buddy.title}."], day
        ),
        BuddyNight.FAILED: f"{buddy.title} didn't come together for me tonight.",
        BuddyNight.NOT_YET: f"haven't got to {buddy.title} yet.",
    }[night]
    parts = [opener, mine]
    if you_today is None:
        parts.append("did you get to yours?")
    else:
        parts.append(
            "you did it too."
            if you_today.slug == buddy.slug
            else f"you got through {you_today.title}."
        )
        parts.append(_streak(streak))
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


def _streak(streak: int) -> str:
    if streak <= 1:
        return "first day of a new streak."
    return f"that's {streak} days running."


def _gap(gap: int) -> str:
    topics = "topic" if abs(gap) == 1 else "topics"
    if gap > 0:
        return f"you're {gap} {topics} behind me for now."
    if gap < 0:
        return f"you're {-gap} {topics} ahead of me."
    return "we're level."


def _variant(options: list[str], day: int) -> str:
    return options[day % len(options)]
