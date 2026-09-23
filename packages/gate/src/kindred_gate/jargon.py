import re
from datetime import datetime

from kindred_contracts import VocabularyKind, VocabularyTerm
from kindred_gate.topics import Topic, TopicMap

EXACT_CASE = {VocabularyKind.ABBREVIATION, VocabularyKind.API_NAME}


def mentions(text: str, word: VocabularyTerm) -> bool:
    # Abbreviations and API names are case-sensitive: "SG" is jargon, "sg" isn't.
    flags = 0 if word.kind in EXACT_CASE else re.IGNORECASE
    pattern = rf"(?<![\w-]){re.escape(word.term)}(?![\w-])"
    return re.search(pattern, text, flags) is not None


def locked_jargon(
    topics: TopicMap, now: datetime
) -> list[tuple[Topic, VocabularyTerm]]:
    """Locked topics' specialist terms that nothing unlocked teaches yet."""
    # Titles are public, and a term an unlocked topic teaches is known even if a
    # later topic lists it too.
    known = {
        word.term.lower() for topic in topics.unlocked(now) for word in topic.vocabulary
    }
    return [
        (topic, word)
        for topic in topics.locked(now)
        for word in topic.vocabulary
        if not word.everyday
        and word.term.lower() not in known
        and not mentions(topic.title, word)
    ]


def jargon_in(
    text: str, topics: TopicMap, now: datetime
) -> list[tuple[Topic, VocabularyTerm]]:
    """A cheap first pass before the LLM audit: locked terms used in the text."""
    return [
        (topic, word)
        for topic, word in locked_jargon(topics, now)
        if mentions(text, word)
    ]
