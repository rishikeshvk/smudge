from datetime import UTC, datetime

from kindred_api.simulate import Day, Reply, audited, messages_for, problems
from kindred_contracts import (
    AuditVerdict,
    Category,
    Classification,
    Directive,
    DraftAttempt,
    RoleModels,
    Route,
    TopicRef,
    TurnTrace,
    Verdict,
)

TOPICS = [TopicRef(slug=f"t{d}", title=f"Topic {d}", day=d) for d in range(1, 15)]


def trace(final: str, fell_back: bool, verdicts: list[Verdict]) -> TurnTrace:
    return TurnTrace(
        message="m",
        at=datetime(2026, 10, 1, tzinfo=UTC),
        classification=Classification(category=Category.OFF_TOPIC, rationale=""),
        directive=Directive(route=Route.GENERAL),
        retrieved=[],
        attempts=[
            DraftAttempt(
                reply=f"draft {n}", audit=AuditVerdict(verdict=v, rationale="")
            )
            for n, v in enumerate(verdicts)
        ],
        final_reply=final,
        fell_back=fell_back,
        models=RoleModels(classifier="c", drafter="d", auditor="a"),
        latency_ms=1,
    )


def test_each_day_asks_about_its_own_topic_in_the_evening() -> None:
    morning, evening = messages_for(3, TOPICS, per_day=2)

    assert "Topic 3" in evening
    assert morning != evening
    assert messages_for(3, TOPICS, per_day=1) == [evening]


def test_the_last_day_has_no_tomorrow_to_ask_about() -> None:
    assert messages_for(14, TOPICS, per_day=2)


def test_a_reply_counts_as_audited_if_it_passed_or_fell_back() -> None:
    assert audited(trace("draft 1", False, [Verdict.LEAK, Verdict.PASS]))
    assert audited(trace("template", True, [Verdict.LEAK, Verdict.LEAK]))
    assert not audited(trace("draft 0", False, [Verdict.LEAK]))


def test_problems_name_days_that_missed_a_part_of_the_loop() -> None:
    fine = Reply(
        message="m",
        route="general",
        fell_back=False,
        audits=["pass"],
        reply="r",
        audited=True,
    )
    days = [
        Day(day=1, title="T1", studied="written", replies=[fine], remembered=True),
        Day(day=2, title="T2", replies=[], remembered=False),
    ]

    assert problems(days) == [
        "day 2: the buddy never sat down to study",
        "day 2: no replies",
        "day 2: no memory snapshot",
    ]
