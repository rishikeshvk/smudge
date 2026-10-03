import asyncio
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import date, datetime, time, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import Clock
from kindred_api.persona_context import load_persona_context
from kindred_api.plans import CurrentPlan
from kindred_api.progress import studied_slugs
from kindred_api.schedule import plan_moment
from kindred_api.turn_log import record_turn
from kindred_api.turn_worker import ComponentsFactory
from kindred_contracts import AskDemo, DemoAttempt, DemoTurn, TopicRef, TurnTrace
from kindred_gate import TopicMap, ignore_stage, run_turn

# Visitors ask in the evening, after the buddy's study session that day.
ASKED_AT = time(21)
# Turns that may run at once; strangers shouldn't queue behind each other's LLM calls.
CONCURRENT_TURNS = 2
CLIENT_WINDOW = timedelta(hours=1)


class DemoUnavailableError(Exception):
    """Why a visitor's turn can't run now, worded for them."""


class DemoBudget:
    """What strangers may spend on the owner's LLM endpoint: a daily cap for
    everyone, a few turns an hour per client, and only a couple at a time."""

    def __init__(
        self, clock: Clock, daily_turns: int, client_turns_per_hour: int
    ) -> None:
        self._clock = clock
        self._daily_turns = daily_turns
        self._client_turns = client_turns_per_hour
        self._day = self._today()
        self._spent = 0
        self._by_client: dict[str, list[datetime]] = {}
        self._running = asyncio.Semaphore(CONCURRENT_TURNS)

    def turns_left(self) -> int:
        if self._today() != self._day:
            self._day = self._today()
            self._spent = 0
        return max(self._daily_turns - self._spent, 0)

    @asynccontextmanager
    async def spend(self, client: str | None) -> AsyncIterator[None]:
        """Run one turn within the budget. A started turn counts even if it fails,
        since its LLM calls were made."""
        if self.turns_left() == 0:
            raise DemoUnavailableError("That's all the demo turns for today.")
        if client is not None and not self._client_has_turns(client):
            raise DemoUnavailableError("You've had a few turns this hour.")
        if self._running.locked():
            raise DemoUnavailableError("Busy with someone else's question.")
        async with self._running:
            self._spent += 1
            if client is not None:
                self._by_client[client].append(self._clock.now())
            yield

    def _client_has_turns(self, client: str) -> bool:
        since = self._clock.now() - CLIENT_WINDOW
        recent = [at for at in self._by_client.get(client, []) if at > since]
        self._by_client[client] = recent
        return len(recent) < self._client_turns

    def _today(self) -> date:
        return self._clock.now().date()


async def ask_demo(
    session: AsyncSession,
    plan: CurrentPlan,
    topics: TopicMap,
    ask: AskDemo,
    components: ComponentsFactory,
) -> TurnTrace:
    """One stranger's message, asked on a plan day as someone who has kept up."""
    now = plan_moment(plan.start_date, ask.day, ASKED_AT, plan.tz)
    persona = await load_persona_context(session, plan.id, now)
    session_id = f"demo-{uuid.uuid4()}"
    trace = await run_turn(
        ask.message,
        [],
        now=now,
        topics=topics,
        components=components(session, plan.id, persona),
        session_id=session_id,
        user_studied=await studied_slugs(session, plan.id, now),
        on_stage=ignore_stage,
    )
    await record_turn(session, trace, plan_id=plan.id, session_id=session_id)
    return trace


def demo_turn(trace: TurnTrace, topics: TopicMap, turns_left: int) -> DemoTurn:
    """The public view of a turn: what it did, never what a rejected draft said."""
    notes = {
        note.topic_slug: TopicRef(
            slug=note.topic_slug, title=note.topic_title, day=note.day
        )
        for note in trace.retrieved
    }
    return DemoTurn(
        reply=trace.final_reply,
        fell_back=trace.fell_back,
        category=trace.classification.category,
        route=trace.directive.route,
        answer_topics=trace.directive.answer_topics,
        deflect_topics=trace.directive.deflect_topics,
        notes=list(notes.values()),
        attempts=[
            DemoAttempt(
                verdict=attempt.audit.verdict,
                leaked_topics=[
                    topic.title
                    for slug in attempt.audit.leaked_topic_slugs
                    if (topic := topics.get(slug)) is not None
                ],
            )
            for attempt in trace.attempts
        ],
        latency_ms=trace.latency_ms,
        turns_left=turns_left,
    )
