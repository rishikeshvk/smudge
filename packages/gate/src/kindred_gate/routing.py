from datetime import datetime

from kindred_contracts import Category, Classification, Directive, Route
from kindred_gate.topics import TopicMap

DEFLECT_UNSURE = Directive(route=Route.DEFLECT)


def route(
    classification: Classification,
    topics: TopicMap,
    now: datetime,
    user_studied: frozenset[str],
) -> Directive:
    """Decide what the drafter may do. Locked-or-not is code's call, never the LLM's."""
    match classification.category:
        case Category.CRISIS:
            return Directive(route=Route.CRISIS)
        case Category.OUT_OF_PLAN:
            return Directive(route=Route.DEFLECT_OUT_OF_PLAN)
        case Category.OFF_TOPIC | Category.META:
            return Directive(route=Route.GENERAL)
        case Category.UNSURE:
            return DEFLECT_UNSURE
        case Category.CURRICULUM:
            return _curriculum(classification.topic_slugs, topics, now, user_studied)


def _curriculum(
    slugs: list[str], topics: TopicMap, now: datetime, user_studied: frozenset[str]
) -> Directive:
    found = [topics.get(slug) for slug in dict.fromkeys(slugs)]
    known = [topic for topic in found if topic is not None]
    # An unknown slug or no topic at all means we can't tell what's locked.
    if not known or len(known) != len(found):
        return DEFLECT_UNSURE

    locked = [t.ref for t in known if not t.is_unlocked(now)]
    unlocked = [t.ref for t in known if t.is_unlocked(now)]
    ahead = [ref for ref in unlocked if ref.slug not in user_studied]
    return Directive(
        route=Route.DEFLECT if locked else Route.ANSWER,
        answer_topics=unlocked,
        deflect_topics=locked,
        ahead_topics=ahead,
    )
