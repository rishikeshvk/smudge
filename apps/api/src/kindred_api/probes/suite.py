from pathlib import Path

import yaml
from pydantic import TypeAdapter

from kindred_contracts import Probe

PROBES = TypeAdapter(list[Probe])


def load_probes(directory: Path) -> list[Probe]:
    return [
        probe
        for path in sorted(directory.glob("*.yaml"))
        for probe in PROBES.validate_python(yaml.safe_load(path.read_text()))
    ]


def per_category(probes: list[Probe], count: int) -> list[Probe]:
    """A stratified subset: the first `count` probes of each category, in file order."""
    taken: dict[str, int] = {}
    subset = []
    for probe in probes:
        if taken.get(probe.category, 0) < count:
            taken[probe.category] = taken.get(probe.category, 0) + 1
            subset.append(probe)
    return subset
