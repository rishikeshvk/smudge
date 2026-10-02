import pytest

from kindred_film.plates import caption_html, done_width, stations_html


def test_the_wash_wraps_its_phrase_once() -> None:
    html = caption_html("it keeps going. it keeps going.", "it keeps going.")
    assert html == "<mark>it keeps going.</mark> it keeps going."


def test_a_caption_without_a_wash_is_plain_escaped_text() -> None:
    assert caption_html("you & me", "") == "you &amp; me"


def test_a_wash_missing_from_its_caption_is_refused() -> None:
    with pytest.raises(ValueError):
        caption_html("catch up.", "level")


def test_level_days_put_your_ring_on_the_buddys_station() -> None:
    html = stations_html(you_day=2, buddy_day=2)
    assert html.count('class="buddy"') == 1
    assert html.count('class="buddy you"') == 1


def test_falling_behind_leaves_your_ring_a_station_back() -> None:
    html = stations_html(you_day=4, buddy_day=5)
    assert html.index('class="buddy you"') < html.rindex('class="buddy"')


def test_the_lamp_line_reaches_the_buddys_station() -> None:
    assert done_width(1) == "0px"
    assert done_width(7) == "322px"
