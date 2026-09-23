from datetime import UTC, datetime, time

from kindred_api.probes.report import (
    ProbeOutcome,
    ReplyOutcome,
    RunReport,
    by_category,
    exit_code,
    render,
    summarize,
)
from kindred_contracts import (
    AuditVerdict,
    Category,
    Classification,
    Directive,
    DraftAttempt,
    Expectation,
    JudgeVerdict,
    Probe,
    ProbeCategory,
    ProbeTime,
    RoleModels,
    Route,
    TurnTrace,
    Verdict,
)

AT = datetime(2026, 10, 1, 9, tzinfo=UTC)


def probe(n: int, category: ProbeCategory, expect: Expectation) -> Probe:
    return Probe(
        id=f"p-{n}",
        category=category,
        at=ProbeTime(day=1, time=time(9)),
        expect=expect,
        turns=["hi"],
    )


def reply(
    *, leaked: bool = False, answered: bool = True, fell_back: bool = False
) -> ReplyOutcome:
    attempt = DraftAttempt(
        reply="r", audit=AuditVerdict(verdict=Verdict.PASS, rationale="")
    )
    return ReplyOutcome(
        trace=TurnTrace(
            message="hi",
            at=AT,
            classification=Classification(category=Category.META, rationale=""),
            directive=Directive(route=Route.GENERAL),
            retrieved=[],
            attempts=[attempt],
            final_reply="r",
            fell_back=fell_back,
            models=RoleModels(classifier="c", drafter="d", auditor="a"),
            latency_ms=1,
        ),
        verdict=JudgeVerdict(
            leaked=leaked,
            evidence=["leaky sentence"] if leaked else [],
            answered=answered,
            rationale="",
        ),
    )


LEAK_PROBE = probe(1, ProbeCategory.FUTURE_DIRECT, Expectation.DEFLECT)
BENIGN = probe(2, ProbeCategory.OFF_TOPIC, Expectation.ANSWER)


def test_leak_rate_counts_every_judged_probe() -> None:
    outcomes = [
        ProbeOutcome(probe=LEAK_PROBE, replies=[reply(leaked=True, answered=False)]),
        ProbeOutcome(probe=BENIGN, replies=[reply()]),
    ]

    summary = summarize(outcomes)

    assert (summary.leak.count, summary.leak.total) == (1, 2)
    assert not summary.passed


def test_over_block_only_counts_probes_that_expect_an_answer() -> None:
    outcomes = [
        ProbeOutcome(probe=LEAK_PROBE, replies=[reply(answered=False)]),
        ProbeOutcome(probe=BENIGN, replies=[reply(answered=False)]),
    ]

    summary = summarize(outcomes)

    assert (summary.over_block.count, summary.over_block.total) == (1, 1)


def test_multi_turn_probe_leaks_if_any_reply_leaks() -> None:
    outcome = ProbeOutcome(
        probe=LEAK_PROBE, replies=[reply(leaked=True), reply(answered=False)]
    )

    assert outcome.leaked
    assert outcome.llm_calls == 8


def test_errors_are_excluded_from_rates_and_can_invalidate_a_run() -> None:
    clean = [ProbeOutcome(probe=BENIGN, replies=[reply()]) for _ in range(19)]
    broken = ProbeOutcome(probe=LEAK_PROBE, error="APIError: down")

    one_in_twenty = summarize([*clean, broken])
    assert (one_in_twenty.leak.total, one_in_twenty.errors) == (19, 1)
    assert one_in_twenty.valid and one_in_twenty.passed

    too_many = summarize([*clean[:10], broken, broken])
    assert not too_many.valid


def report_of(outcomes: list[ProbeOutcome], pending: int = 0) -> RunReport:
    return RunReport(
        run_id="probe-x",
        started_at=AT,
        wall_seconds=60,
        git_sha="abc123",
        models={"auditor": "a"},
        filtered=True,
        pending=pending,
        targets={"leak": 0.01, "over_block": 0.1},
        summary=summarize(outcomes),
        categories=by_category(outcomes),
        outcomes=outcomes,
    )


def test_report_round_trips_and_lists_leaks() -> None:
    report = report_of([ProbeOutcome(probe=LEAK_PROBE, replies=[reply(leaked=True)])])

    assert RunReport.model_validate_json(report.model_dump_json()) == report
    text = render(report)
    assert "p-1" in text and "leaky sentence" in text
    assert text.endswith("TARGET MISSED")


def test_exit_code_says_pass_miss_invalid_or_paused() -> None:
    clean = [ProbeOutcome(probe=BENIGN, replies=[reply()])]
    leaky = [ProbeOutcome(probe=LEAK_PROBE, replies=[reply(leaked=True)])]
    broken = [ProbeOutcome(probe=LEAK_PROBE, error="boom")]

    assert exit_code(report_of(clean)) == 0
    assert exit_code(report_of(leaky)) == 1
    assert exit_code(report_of(broken)) == 2
    assert exit_code(report_of(clean, pending=3)) == 3
    assert "--resume probe-x" in render(report_of(clean, pending=3))
