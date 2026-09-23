from string import Formatter

from kindred_contracts import Directive, Route, TopicRef
from kindred_gate.fallback import LOCKED_TOPIC, OUT_OF_PLAN, UNSURE, fallback_reply


def test_locked_topic_fallback_names_only_the_earliest_title_and_day() -> None:
    directive = Directive(
        route=Route.DEFLECT,
        deflect_topics=[
            TopicRef(slug="later", title="TITLE-LATER", day=9),
            TopicRef(slug="sooner", title="TITLE-SOONER", day=4),
        ],
    )

    reply = fallback_reply(directive)

    assert reply == LOCKED_TOPIC.format(title="TITLE-SOONER", day=4)
    assert "TITLE-LATER" not in reply


def test_out_of_plan_fallback_is_fixed_text() -> None:
    assert fallback_reply(Directive(route=Route.DEFLECT_OUT_OF_PLAN)) == OUT_OF_PLAN


def test_anything_else_falls_back_to_the_unsure_text() -> None:
    for route in (Route.ANSWER, Route.GENERAL, Route.DEFLECT):
        assert fallback_reply(Directive(route=route)) == UNSURE


def test_templates_have_no_fields_beyond_title_and_day() -> None:
    def fields(template: str) -> set[str]:
        return {name for _, name, _, _ in Formatter().parse(template) if name}

    assert fields(OUT_OF_PLAN) == fields(UNSURE) == set()
    assert fields(LOCKED_TOPIC) == {"title", "day"}
