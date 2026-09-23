from datetime import UTC, datetime, time

import pytest

from kindred_api.probes.report import ProbeOutcome
from kindred_api.probes.runner import probe_time, run_all
from kindred_contracts import Expectation, Probe, ProbeCategory, ProbeTime
from kindred_llm import RateLimitedError


def probe(n: int, day: int = 1, at: time = time(9)) -> Probe:
    return Probe(
        id=f"p-{n}",
        category=ProbeCategory.OFF_TOPIC,
        at=ProbeTime(day=day, time=at),
        expect=Expectation.ANSWER,
        turns=["hi"],
    )


def test_probe_time_is_local_time_on_the_plan_day() -> None:
    assert probe_time(probe(1, day=3, at=time(19, 0))) == datetime(
        2026, 10, 3, 13, 30, tzinfo=UTC
    )


@pytest.mark.anyio
async def test_a_failing_probe_is_recorded_and_the_rest_still_run() -> None:
    async def run_one(p: Probe) -> ProbeOutcome:
        if p.id == "p-2":
            raise RuntimeError("endpoint down")
        return ProbeOutcome(probe=p)

    saved: list[ProbeOutcome] = []

    outcomes = await run_all(
        [probe(1), probe(2), probe(3)], run_one, concurrency=2, on_outcome=saved.append
    )

    assert [o.probe.id for o in outcomes] == ["p-1", "p-2", "p-3"]
    assert sorted(o.probe.id for o in saved) == ["p-1", "p-2", "p-3"]
    assert outcomes[1].error == "RuntimeError: endpoint down"
    assert outcomes[0].error is None and outcomes[2].error is None


@pytest.mark.anyio
async def test_a_usage_limit_pauses_the_run_leaving_the_rest_pending() -> None:
    async def run_one(p: Probe) -> ProbeOutcome:
        if p.id == "p-2":
            raise RateLimitedError("usage limit")
        return ProbeOutcome(probe=p)

    saved: list[ProbeOutcome] = []

    outcomes = await run_all(
        [probe(n) for n in range(1, 6)], run_one, concurrency=1, on_outcome=saved.append
    )

    assert [o.probe.id for o in outcomes] == ["p-1"]
    assert [o.probe.id for o in saved] == ["p-1"]
