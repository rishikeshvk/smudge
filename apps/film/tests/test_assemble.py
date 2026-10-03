from pathlib import Path

import pytest

from kindred_film.assemble import (
    VOICE_IN,
    Tap,
    VoiceTooLong,
    caption_lift,
    card_command,
    check_voice_fits,
    join_command,
    scene_starts,
    shot_command,
    shot_taps,
    voice_command,
    xfade_offsets,
)
from kindred_film.frame import SCREEN
from kindred_film.scenes import Card, Cut, Shot

SHOT = Shot(
    id="99",
    ground="night",
    meta="day 3 · 21:00",
    caption="a caption.",
    wash="",
    voice="a line.",
    you_day=3,
    buddy_day=3,
    cuts=(Cut("a", 2, 6), Cut("b", 1, 5)),
    push=(1, 3),
)


def _graph(command: list[str]) -> str:
    return command[command.index("-filter_complex") + 1]


def test_crossfades_overlap_each_join_by_the_same_amount() -> None:
    assert xfade_offsets([7, 17, 12], 0.5) == [6.5, 23.0]


def test_taps_move_onto_the_shot_timeline_and_the_frame() -> None:
    taps = {
        "a": [Tap(t=3, x=0, y=0), Tap(t=9, x=0, y=0)],
        "b": [Tap(t=2, x=1080, y=2400)],
    }
    placed = shot_taps(SHOT, taps)
    assert placed == [
        Tap(t=1, x=SCREEN.x, y=SCREEN.y),
        Tap(t=5, x=SCREEN.x + SCREEN.w, y=SCREEN.y + SCREEN.h),
    ]


def test_a_shot_reads_each_cut_and_draws_one_ring_per_tap() -> None:
    taps = [Tap(t=1, x=1300, y=900), Tap(t=5, x=1400, y=700)]
    command = shot_command(SHOT, taps, Path("out.mp4"))
    graph = _graph(command)
    assert command.count("-i") == 1 + 2 + 2 + 2
    assert "concat=n=2" in graph
    assert graph.count("[ring") == 4
    assert "zoompan" in graph


def test_a_shot_without_a_push_keeps_the_frame_still() -> None:
    still = Shot(**{**SHOT.__dict__, "push": None})
    assert "zoompan" not in _graph(shot_command(still, [], Path("out.mp4")))


def test_the_caption_settles_after_its_rise() -> None:
    assert caption_lift(0.4).startswith("12*pow(1-min(1,max(0,(t-0.4)/0.45))")


def test_only_the_last_card_fades_to_black() -> None:
    card = Card(id="10", template="card-end", seconds=8, voice="a line.")
    assert "fade=out" in " ".join(card_command(card, last=True, out=Path("x.mp4")))
    assert "fade=in" in " ".join(card_command(card, last=False, out=Path("x.mp4")))


def test_the_picture_is_joined_without_sound() -> None:
    command = join_command([Path("a.mp4"), Path("b.mp4")], [5, 5], 0.5, Path("f.mp4"))
    assert "-an" in command
    assert "xfade=transition=fade:duration=0.5:offset=4.5" in _graph(command)


def test_each_scene_starts_where_its_crossfade_begins() -> None:
    assert scene_starts([7, 17, 12], 0.5) == [0.0, 6.5, 23.0]


def test_each_line_is_placed_just_after_its_scene_starts() -> None:
    voices = [Path("01.mp3"), Path("02.mp3")]
    graph = _graph(voice_command(Path("p.mp4"), voices, [0.0, 6.5], Path("f.mp4")))
    assert f"[1:a]adelay=delays={round(VOICE_IN * 1000)}:all=1" in graph
    assert f"[2:a]adelay=delays={round((6.5 + VOICE_IN) * 1000)}:all=1" in graph
    assert "amix=inputs=2" in graph


def test_the_voice_is_loudness_normalised_and_the_picture_is_not_re_encoded() -> None:
    command = voice_command(Path("p.mp4"), [Path("01.mp3")], [0.0], Path("f.mp4"))
    assert "loudnorm=I=-14" in _graph(command)
    assert command[command.index("-c:v") + 1] == "copy"


def test_a_line_longer_than_its_scene_is_refused() -> None:
    check_voice_fits("03", scene_seconds=10, voice_seconds=8)
    with pytest.raises(VoiceTooLong):
        check_voice_fits("03", scene_seconds=10, voice_seconds=9.5)


def test_each_cut_holds_its_last_frame_to_its_full_length() -> None:
    graph = _graph(shot_command(SHOT, [], Path("out.mp4")))
    assert "tpad=stop_mode=clone:stop_duration=4" in graph
    assert "trim=duration=4" in graph
