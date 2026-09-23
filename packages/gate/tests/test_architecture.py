import re
from pathlib import Path

ROOT = Path(__file__).parents[3]
GATED = re.compile(
    r"\bLedgerNote\b|\bledger_notes\b|\bSourceDocument\b|\bsource_documents\b"
)

# Invariant 2: gated knowledge is read in one module, through one unlock filter.
# The other files define the tables or only ever write to them.
ALLOWED = {
    "packages/db/src/kindred_db/models.py",
    "packages/db/src/kindred_db/__init__.py",
    "packages/gate/src/kindred_gate/retrieval.py",
    "apps/api/src/kindred_api/seed.py",
    "apps/api/src/kindred_api/ingest.py",
    "apps/api/src/kindred_api/ledger.py",
}


def source_files() -> list[Path]:
    return [
        path
        for pattern in ("apps/*/src/**/*.py", "packages/*/src/**/*.py")
        for path in ROOT.glob(pattern)
    ]


def test_only_the_retrieval_module_reads_gated_knowledge() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for path in source_files()
        if str(path.relative_to(ROOT)) not in ALLOWED and GATED.search(path.read_text())
    ]

    assert offenders == []
