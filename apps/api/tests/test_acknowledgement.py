import pytest

from kindred_api.acknowledgement import reaction_to


@pytest.mark.parametrize(
    ("message", "emoji"),
    [
        ("ok", "👍"),
        ("Ok!!", "👍"),
        ("sounds  good.", "👍"),
        ("thanks", "❤️"),
        ("haha", "😄"),
        ("gn", "🌙"),
        ("👍", "❤️"),
    ],
)
def test_an_acknowledgement_gets_a_reaction(message: str, emoji: str) -> None:
    assert reaction_to(message, "we're level.") == emoji


def test_an_ok_to_a_question_is_an_answer() -> None:
    assert reaction_to("ok", "you around then too?") is None


@pytest.mark.parametrize(
    "message",
    ["ok but why regions?", "thanks, what's next?", "I want to die", "not today", ""],
)
def test_anything_with_content_gets_a_reply(message: str) -> None:
    assert reaction_to(message, None) is None
