import argparse
import asyncio
import subprocess
import time
from pathlib import Path

from kindred_api.clock import SystemClock
from kindred_api.config import get_settings
from kindred_api.probes.report import (
    LEAK_TARGET,
    OVER_BLOCK_TARGET,
    ProbeOutcome,
    RunReport,
    by_category,
    exit_code,
    render,
    summarize,
)
from kindred_api.probes.runner import run_probes
from kindred_api.probes.suite import load_probes, per_category
from kindred_contracts import ProbeCategory


def git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    )
    return result.stdout.strip() or "unknown"


def load_partial(path: Path) -> list[ProbeOutcome]:
    if not path.exists():
        return []
    return [
        ProbeOutcome.model_validate_json(line)
        for line in path.read_text().splitlines()
        if line
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure leak and over-block rates.")
    parser.add_argument("--category", type=ProbeCategory, action="append")
    parser.add_argument("--per-category", type=int, help="stratified subset size")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--resume", metavar="RUN_ID", help="continue a paused run")
    parser.add_argument("--probes", type=Path, default=Path("evals/probes"))
    parser.add_argument(
        "--curriculum", type=Path, default=Path("curricula/aws-2week.yaml")
    )
    parser.add_argument("--results", type=Path, default=Path("evals/results"))
    args = parser.parse_args()

    probes = load_probes(args.probes)
    if args.category:
        probes = [p for p in probes if p.category in args.category]
    if args.per_category:
        probes = per_category(probes, args.per_category)
    if args.limit:
        probes = probes[: args.limit]
    filtered = len(probes) < len(load_probes(args.probes))

    started_at = SystemClock().now()
    run_id = args.resume or f"probe-{started_at:%Y%m%dT%H%M%SZ}"
    args.results.mkdir(parents=True, exist_ok=True)
    partial = args.results / f"{run_id}.partial.jsonl"
    done = load_partial(partial)
    done_ids = {o.probe.id for o in done}
    todo = [p for p in probes if p.id not in done_ids]

    def save(outcome: ProbeOutcome) -> None:
        with partial.open("a") as file:
            file.write(outcome.model_dump_json() + "\n")

    settings = get_settings()
    started = time.monotonic()
    fresh = asyncio.run(
        run_probes(
            todo,
            settings=settings,
            curriculum_path=args.curriculum,
            run_id=run_id,
            concurrency=args.concurrency,
            fresh=args.resume is None,
            on_outcome=save,
        )
    )
    outcomes = [*done, *fresh]
    report = RunReport(
        run_id=run_id,
        started_at=started_at,
        wall_seconds=time.monotonic() - started,
        git_sha=git_sha(),
        models={
            "classifier": settings.llm_model_classifier,
            "drafter": settings.llm_model_drafter,
            "auditor": settings.llm_model_auditor,
            "judge": settings.llm_model_judge,
            "embeddings": settings.embed_model,
        },
        filtered=filtered,
        pending=len(probes) - len(outcomes),
        targets={"leak": LEAK_TARGET, "over_block": OVER_BLOCK_TARGET},
        summary=summarize(outcomes),
        categories=by_category(outcomes),
        outcomes=outcomes,
    )

    print()
    print(render(report))
    if not report.pending:
        path = args.results / f"{run_id}.json"
        path.write_text(report.model_dump_json(indent=2))
        partial.unlink(missing_ok=True)
        print(f"\nSaved {path}")
    raise SystemExit(exit_code(report))


if __name__ == "__main__":
    main()
