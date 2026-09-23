import re
from pathlib import Path

ROOT = Path(__file__).parents[3]
LEDGER = re.compile(r"\bLedgerNote\b|\bledger_notes\b")

# Invariant 2: one function reads the ledger. The others define or write it.
ALLOWED = {
    "packages/db/src/kindred_db/models.py",
    "packages/db/src/kindred_db/__init__.py",
    "packages/gate/src/kindred_gate/retrieval.py",
    "apps/api/src/kindred_api/seed.py",
}


def source_files() -> list[Path]:
    return [
        path
        for pattern in ("apps/*/src/**/*.py", "packages/*/src/**/*.py")
        for path in ROOT.glob(pattern)
    ]


def test_only_the_gated_retrieval_function_reads_the_ledger() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for path in source_files()
        if str(path.relative_to(ROOT)) not in ALLOWED
        and LEDGER.search(path.read_text())
    ]

    assert offenders == []
