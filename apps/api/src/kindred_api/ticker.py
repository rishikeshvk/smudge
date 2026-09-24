import asyncio
import logging
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.clock import Clock
from kindred_api.director import RitualSchedule, send_due_rituals
from kindred_api.plans import CurrentPlan, load_current_plan
from kindred_api.relationship import Rememberer, remember_day, unremembered_days
from kindred_api.study import StudyComponents, due_topics, study_topic
from kindred_llm import LLMUnavailableError

TICK_SECONDS = 60

logger = logging.getLogger(__name__)


class Ticker:
    """The buddy's life on a schedule: each tick catches up on whatever is due by
    the Clock's now, so dev time jumps and missed ticks both come out right."""

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        clock: Clock,
        study: Callable[[], StudyComponents],
        memory: Callable[[], Rememberer],
        rituals: RitualSchedule,
    ) -> None:
        self._sessions = sessions
        self._clock = clock
        self._study = study
        self._memory = memory
        self.rituals = rituals
        self._lock = asyncio.Lock()
        self.studying = False

    async def run(self) -> None:
        while True:
            try:
                await self.tick()
            except Exception:
                logger.exception("tick failed")
            await asyncio.sleep(TICK_SECONDS)

    async def tick(self) -> None:
        async with self._lock, self._sessions() as session:
            plan = await load_current_plan(session)
            if plan is None:
                return
            try:
                await self._study_due(session, plan.id)
                await self._remember_due(session, plan)
            except LLMUnavailableError:
                await session.rollback()
                logger.warning("model endpoint unavailable; trying again next tick")
            # Rituals are templates and the stored share, so they go out even while
            # the endpoint is down.
            await self._send_rituals(session, plan)

    async def _study_due(self, session: AsyncSession, plan_id: int) -> None:
        due = await due_topics(session, plan_id, self._clock.now())
        if not due:
            return
        self.studying = True
        try:
            for node in due:
                outcome = await study_topic(
                    session, node, self._clock.now(), self._study()
                )
                await session.commit()
                logger.info("studied day %s: %s", node.day, outcome.status.value)
        finally:
            self.studying = False

    async def _remember_due(self, session: AsyncSession, plan: CurrentPlan) -> None:
        now = self._clock.now()
        for day in await unremembered_days(session, plan.user_id, plan.tz, now):
            await remember_day(session, plan.user_id, day, plan.tz, now, self._memory())
            await session.commit()
            logger.info("remembered %s", day)

    async def _send_rituals(self, session: AsyncSession, plan: CurrentPlan) -> None:
        sent = await send_due_rituals(session, plan, self.rituals, self._clock.now())
        await session.commit()
        for message in sent:
            logger.info("sent a ritual: %s", message.text)
