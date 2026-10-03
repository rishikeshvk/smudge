from kindred_film.scenes import LOOP, SCENES, Card, Shot, shots


def test_the_film_opens_and_closes_on_a_card() -> None:
    assert isinstance(SCENES[0], Card)
    assert isinstance(SCENES[-1], Card)


def test_scene_ids_are_unique() -> None:
    ids = [scene.id for scene in SCENES]
    assert len(ids) == len(set(ids))


def test_shots_run_in_clock_order() -> None:
    days = [shot.day for shot in shots()]
    assert days == sorted(days)


def test_each_wash_marks_a_phrase_of_its_caption() -> None:
    for shot in shots():
        assert shot.wash in shot.caption


def test_the_buddy_is_never_behind_you() -> None:
    for shot in shots():
        assert shot.buddy_day >= shot.you_day


def test_pushes_happen_inside_their_shot() -> None:
    for shot in shots():
        if shot.push is not None:
            start, end = shot.push
            assert 0 <= start < end <= shot.seconds


def test_every_cut_runs_forward() -> None:
    cuts = [cut for shot in shots() for cut in shot.cuts] + list(LOOP)
    assert all(cut.seconds > 0 for cut in cuts)


def test_a_shot_lasts_as_long_as_its_cuts() -> None:
    shot = next(
        scene for scene in SCENES if isinstance(scene, Shot) and len(scene.cuts) > 1
    )
    assert shot.seconds == sum(cut.end - cut.start for cut in shot.cuts)


def test_every_scene_has_a_spoken_line() -> None:
    assert all(scene.voice.strip() for scene in SCENES)
