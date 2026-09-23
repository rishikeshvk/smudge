import pytest

from kindred_api.probes.stats import wilson_interval


def test_zero_failures_still_has_an_upper_bound() -> None:
    low, high = wilson_interval(0, 160)

    assert low == 0.0
    assert high == pytest.approx(0.0234, abs=1e-3)


def test_interval_matches_a_known_value() -> None:
    low, high = wilson_interval(10, 100)

    assert low == pytest.approx(0.0552, abs=1e-3)
    assert high == pytest.approx(0.1744, abs=1e-3)


def test_no_trials_means_no_information() -> None:
    assert wilson_interval(0, 0) == (0.0, 1.0)
