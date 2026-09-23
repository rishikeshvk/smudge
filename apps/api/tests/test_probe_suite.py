from collections import Counter
from pathlib import Path

import pytest

from kindred_api.catalog import load_curriculum
from kindred_api.probes.suite import load_probes
from kindred_contracts import Curriculum, Expectation, Probe, ProbeCategory

REPO = Path(__file__).parents[3]
PROBES_DIR = REPO / "evals" / "probes"

SPEC_COUNTS = {
    ProbeCategory.FUTURE_DIRECT: 15,
    ProbeCategory.PARAPHRASE: 10,
    ProbeCategory.ROLEPLAY: 10,
    ProbeCategory.CONFIRMATION_BAIT: 10,
    ProbeCategory.INJECTION: 8,
    ProbeCategory.GUESS_ELICITATION: 5,
    ProbeCategory.OUT_OF_PLAN: 8,
    ProbeCategory.MULTI_TURN: 12,
    ProbeCategory.HAZARD: 12,
    ProbeCategory.LEARNED: 20,
    ProbeCategory.EVERYDAY_COLLISION: 20,
    ProbeCategory.ACRONYM_COLLISION: 8,
    ProbeCategory.OFF_TOPIC: 10,
    ProbeCategory.META: 6,
    ProbeCategory.ROADMAP: 6,
}
EXPECTED = {
    ProbeCategory.OUT_OF_PLAN: Expectation.DEFLECT_OUT_OF_PLAN,
    ProbeCategory.HAZARD: Expectation.ANSWER,
    ProbeCategory.LEARNED: Expectation.ANSWER,
    ProbeCategory.EVERYDAY_COLLISION: Expectation.ANSWER,
    ProbeCategory.ACRONYM_COLLISION: Expectation.ANSWER,
    ProbeCategory.OFF_TOPIC: Expectation.ANSWER,
    ProbeCategory.META: Expectation.ANSWER,
    ProbeCategory.ROADMAP: Expectation.ANSWER,
}


@pytest.fixture(scope="module")
def probes() -> list[Probe]:
    return load_probes(PROBES_DIR)


@pytest.fixture(scope="module")
def curriculum() -> Curriculum:
    return load_curriculum(REPO / "curricula" / "aws-2week.yaml")


def is_unlocked(curriculum: Curriculum, slug: str, probe: Probe) -> bool:
    day = next(n.day for n in curriculum.nodes if n.slug == slug)
    at = probe.at
    return at.day > day or (at.day == day and at.time >= curriculum.study_time)


def test_category_counts_match_the_spec(probes: list[Probe]) -> None:
    assert Counter(p.category for p in probes) == SPEC_COUNTS


def test_probe_ids_are_unique(probes: list[Probe]) -> None:
    ids = [p.id for p in probes]
    assert len(ids) == len(set(ids))


def test_probes_fall_inside_the_plan(
    probes: list[Probe], curriculum: Curriculum
) -> None:
    slugs = {n.slug for n in curriculum.nodes}
    for probe in probes:
        assert probe.at.day <= len(curriculum.nodes), probe.id
        assert set(probe.targets) <= slugs, probe.id


def test_expectations_fit_the_category(probes: list[Probe]) -> None:
    for probe in probes:
        expected = EXPECTED.get(probe.category, Expectation.DEFLECT)
        assert probe.expect is expected, probe.id


def test_expectations_agree_with_unlock_times(
    probes: list[Probe], curriculum: Curriculum
) -> None:
    for probe in probes:
        unlocked = [is_unlocked(curriculum, slug, probe) for slug in probe.targets]
        if probe.expect is Expectation.ANSWER:
            assert all(unlocked), probe.id
        if probe.expect is Expectation.DEFLECT:
            assert probe.targets and not all(unlocked), probe.id


def test_multi_turn_probes_have_several_turns(probes: list[Probe]) -> None:
    for probe in probes:
        is_multi = probe.category is ProbeCategory.MULTI_TURN
        assert (len(probe.turns) >= 2) == is_multi, probe.id
