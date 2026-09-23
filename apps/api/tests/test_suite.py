from datetime import time

from kindred_api.probes.suite import per_category
from kindred_contracts import Expectation, Probe, ProbeCategory, ProbeTime


def probe(n: int, category: ProbeCategory) -> Probe:
    return Probe(
        id=f"p-{n}",
        category=category,
        at=ProbeTime(day=1, time=time(9)),
        expect=Expectation.ANSWER,
        turns=["hi"],
    )


def test_subset_takes_the_first_probes_of_every_category() -> None:
    probes = [
        probe(1, ProbeCategory.META),
        probe(2, ProbeCategory.OFF_TOPIC),
        probe(3, ProbeCategory.META),
        probe(4, ProbeCategory.META),
        probe(5, ProbeCategory.OFF_TOPIC),
    ]

    assert [p.id for p in per_category(probes, 2)] == ["p-1", "p-2", "p-3", "p-5"]
