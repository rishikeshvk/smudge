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
