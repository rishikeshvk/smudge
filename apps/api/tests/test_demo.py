from datetime import UTC, datetime, timedelta

import pytest

from kindred_api.clock import FixedClock
from kindred_api.demo import DemoBudget, DemoUnavailableError, demo_turn
from kindred_contracts import (
    AuditVerdict,
    Category,
    Classification,
    Directive,
    DraftAttempt,
    RetrievedNote,
    RoleModels,
    Route,
    TurnTrace,
    Verdict,
)
from kindred_gate import Topic, TopicMap

NOW = datetime(2026, 10, 3, 15, 0, tzinfo=UTC)


async def spend(budget: DemoBudget, client: str | None = None) -> None:
    async with budget.spend(client):
        pass


@pytest.mark.anyio
async def test_the_daily_cap_is_shared_and_resets_the_next_day() -> None:
    clock = FixedClock(NOW)
    budget = DemoBudget(clock, daily_turns=2, client_turns_per_hour=5)

    await spend(budget, "a")
    await spend(budget, "b")

    assert budget.turns_left() == 0
    with pytest.raises(DemoUnavailableError):
        await spend(budget, "c")
    clock.advance(timedelta(days=1))
    assert budget.turns_left() == 2


@pytest.mark.anyio
async def test_a_zero_cap_turns_the_demo_off() -> None:
    budget = DemoBudget(FixedClock(NOW), daily_turns=0, client_turns_per_hour=5)

    with pytest.raises(DemoUnavailableError):
        await spend(budget)


@pytest.mark.anyio
async def test_one_client_gets_a_few_turns_an_hour() -> None:
    clock = FixedClock(NOW)
    budget = DemoBudget(clock, daily_turns=30, client_turns_per_hour=2)

    await spend(budget, "a")
    await spend(budget, "a")

    with pytest.raises(DemoUnavailableError):
        await spend(budget, "a")
    await spend(budget, "b")
    clock.advance(timedelta(hours=1, seconds=1))
    await spend(budget, "a")


@pytest.mark.anyio
async def test_unknown_clients_only_meet_the_daily_cap() -> None:
    budget = DemoBudget(FixedClock(NOW), daily_turns=3, client_turns_per_hour=1)

    await spend(budget)
    await spend(budget)

    assert budget.turns_left() == 1


@pytest.mark.anyio
async def test_only_two_turns_run_at_once() -> None:
    budget = DemoBudget(FixedClock(NOW), daily_turns=30, client_turns_per_hour=5)

    async with budget.spend("a"), budget.spend("b"):
        with pytest.raises(DemoUnavailableError):
            await spend(budget, "c")
    await spend(budget, "c")


@pytest.mark.anyio
async def test_a_failed_turn_still_counts() -> None:
    budget = DemoBudget(FixedClock(NOW), daily_turns=2, client_turns_per_hour=5)

    with pytest.raises(RuntimeError):
        async with budget.spend("a"):
            raise RuntimeError

    assert budget.turns_left() == 1


def topic(day: int) -> Topic:
    return Topic(
        slug=f"topic-{day}",
        day=day,
        title=f"Topic {day}",
        audit_brief="",
        unlock_at=NOW,
        vocabulary=[],
    )


def note(day: int, note_id: int) -> RetrievedNote:
    return RetrievedNote(
        note_id=note_id,
        topic_slug=f"topic-{day}",
        topic_title=f"Topic {day}",
        day=day,
        body="secret body",
        shaky=[],
        sorted=[],
        distance=0.1,
    )


def test_the_public_turn_names_leaks_but_never_quotes_a_rejected_draft() -> None:
    trace = TurnTrace(
        message="what's tomorrow?",
        at=NOW,
        classification=Classification(category=Category.CURRICULUM, rationale="r"),
        directive=Directive(route=Route.ANSWER, answer_topics=[topic(1).ref]),
        retrieved=[note(1, 1), note(1, 2)],
        attempts=[
            DraftAttempt(
                reply="LOCKED DETAIL",
                audit=AuditVerdict(
                    verdict=Verdict.LEAK,
                    leaked_topic_slugs=["topic-2"],
                    evidence=["LOCKED DETAIL"],
                    rationale="leaks day 2",
                ),
            ),
            DraftAttempt(
                reply="not there yet!",
                audit=AuditVerdict(verdict=Verdict.PASS, rationale="fine"),
            ),
        ],
        final_reply="not there yet!",
        fell_back=False,
        models=RoleModels(classifier="c", drafter="d", auditor="a"),
        latency_ms=900,
    )
    topics = TopicMap(plan_id=1, baseline_card=[], topics=[topic(1), topic(2)])

    turn = demo_turn(trace, topics, turns_left=7)

    assert "LOCKED DETAIL" not in turn.model_dump_json()
    assert "secret body" not in turn.model_dump_json()
    assert [a.leaked_topics for a in turn.attempts] == [["Topic 2"], []]
    assert [n.title for n in turn.notes] == ["Topic 1"]
    assert (turn.reply, turn.turns_left) == ("not there yet!", 7)
