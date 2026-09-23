from datetime import UTC, datetime, time

import pytest

from kindred_api.probes.report import ProbeOutcome
from kindred_api.probes.runner import probe_time, run_all
from kindred_contracts import Expectation, Probe, ProbeCategory, ProbeTime


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

    outcomes = await run_all([probe(1), probe(2), probe(3)], run_one, concurrency=2)

    assert [o.probe.id for o in outcomes] == ["p-1", "p-2", "p-3"]
    assert outcomes[1].error == "RuntimeError: endpoint down"
    assert outcomes[0].error is None and outcomes[2].error is None
