import asyncio
import contextlib
import logging
from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.chat import add_reply, history_before, next_queued
from kindred_api.clock import Clock
from kindred_api.persona_context import load_persona_context
from kindred_api.plans import load_current_plan
from kindred_api.progress import studied_slugs
from kindred_api.turn_log import record_turn
from kindred_contracts import PersonaContext, TurnStage
from kindred_db import Message
from kindred_gate import TurnComponents, load_topic_map, run_turn
from kindred_llm import LLMUnavailableError

RETRY_SECONDS = 60

logger = logging.getLogger(__name__)

ComponentsFactory = Callable[[AsyncSession, int, PersonaContext], TurnComponents]


class TurnWorker:
    """Answers queued messages one at a time, oldest first, so replies see history."""

    def __init__(
        self,
        sessions: async_sessionmaker[AsyncSession],
        clock: Clock,
        components: ComponentsFactory,
    ) -> None:
        self._sessions = sessions
        self._clock = clock
        self._components = components
        self._wake = asyncio.Event()
        self.available = True

    def wake(self) -> None:
        self._wake.set()

    async def run(self) -> None:
        while True:
            self._wake.clear()
            await self.drain()
            # Also retries the queue while the endpoint is down.
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(self._wake.wait(), RETRY_SECONDS)

    async def drain(self) -> None:
        while True:
            async with self._sessions() as session:
                message = await next_queued(session)
                if message is None:
                    return
                message_id = message.id
                try:
                    await self._answer(session, message)
                except LLMUnavailableError:
                    await _restart(session, message_id, TurnStage.QUEUED)
                    self.available = False
                    return
                except Exception:
                    logger.exception("turn failed for message %s", message_id)
                    await _restart(session, message_id, TurnStage.FAILED)
                    continue
                self.available = True

    async def _answer(self, session: AsyncSession, message: Message) -> None:
        plan = await load_current_plan(session)
        if plan is None:
            raise LookupError("a message was queued before there was a plan")
        now = self._clock.now()

        async def report(stage: TurnStage) -> None:
            await _set_stage(session, message, stage)

        persona = await load_persona_context(session, plan.id, now)
        session_id = f"chat-{message.user_id}"
        trace = await run_turn(
            message.text,
            await history_before(session, message, now),
            now=now,
            topics=await load_topic_map(session, plan.id),
            components=self._components(session, plan.id, persona),
            session_id=session_id,
            user_studied=await studied_slugs(session, plan.id, now),
            on_stage=report,
        )
        turn = await record_turn(session, trace, plan_id=plan.id, session_id=session_id)
        await add_reply(session, message, trace.final_reply, turn.id, self._clock.now())
        message.stage = TurnStage.ANSWERED.value
        await session.commit()


async def _set_stage(session: AsyncSession, message: Message, stage: TurnStage) -> None:
    # Committed at once so the app's poll sees each stage as it happens.
    message.stage = stage.value
    await session.commit()


async def _restart(session: AsyncSession, message_id: int, stage: TurnStage) -> None:
    """Drop the half-done turn and park the message at a stage."""
    await session.rollback()
    await _set_stage(session, await session.get_one(Message, message_id), stage)
