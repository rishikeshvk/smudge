import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.clock import Clock
from kindred_api.plans import load_current_plan
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
        study: StudyComponents,
    ) -> None:
        self._sessions = sessions
        self._clock = clock
        self._study = study
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
            await self._study_due(session, plan.id)

    async def _study_due(self, session: AsyncSession, plan_id: int) -> None:
        due = await due_topics(session, plan_id, self._clock.now())
        if not due:
            return
        self.studying = True
        try:
            for node in due:
                outcome = await study_topic(
                    session, node, self._clock.now(), self._study
                )
                await session.commit()
                logger.info("studied day %s: %s", node.day, outcome.status.value)
        except LLMUnavailableError:
            await session.rollback()
            logger.warning("model endpoint unavailable; studying again next tick")
        finally:
            self.studying = False
