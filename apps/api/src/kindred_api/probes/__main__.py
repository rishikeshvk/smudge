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
    RunReport,
    by_category,
    exit_code,
    render,
    summarize,
)
from kindred_api.probes.runner import run_probes
from kindred_api.probes.suite import load_probes
from kindred_contracts import ProbeCategory


def git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True
    )
    return result.stdout.strip() or "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure leak and over-block rates.")
    parser.add_argument("--category", type=ProbeCategory, action="append")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--probes", type=Path, default=Path("evals/probes"))
    parser.add_argument(
        "--curriculum", type=Path, default=Path("curricula/aws-2week.yaml")
    )
    parser.add_argument("--results", type=Path, default=Path("evals/results"))
    args = parser.parse_args()

    probes = load_probes(args.probes)
    if args.category:
        probes = [p for p in probes if p.category in args.category]
    if args.limit:
        probes = probes[: args.limit]
    filtered = bool(args.category or args.limit)

    settings = get_settings()
    started_at = SystemClock().now()
    run_id = f"probe-{started_at:%Y%m%dT%H%M%SZ}"
    started = time.monotonic()
    outcomes = asyncio.run(
        run_probes(
            probes,
            settings=settings,
            curriculum_path=args.curriculum,
            run_id=run_id,
            concurrency=args.concurrency,
        )
    )

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
        targets={"leak": LEAK_TARGET, "over_block": OVER_BLOCK_TARGET},
        summary=summarize(outcomes),
        categories=by_category(outcomes),
        outcomes=outcomes,
    )
    args.results.mkdir(parents=True, exist_ok=True)
    path = args.results / f"{run_id}.json"
    path.write_text(report.model_dump_json(indent=2))

    print()
    print(render(report))
    print(f"\nSaved {path}")
    raise SystemExit(exit_code(report.summary))


if __name__ == "__main__":
    main()
