import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from kindred_api.chat import requeue_interrupted
from kindred_api.config import get_settings
from kindred_api.dependencies import Services
from kindred_api.dev_clock import build_clock
from kindred_api.llm_runtime import LLMRuntime
from kindred_api.llm_settings import effective, load_saved
from kindred_api.routes import (
    buddy,
    chat,
    dev,
    health,
    notebook,
    onboarding,
    progress,
    roadmap,
    settings,
    turns,
)
from kindred_api.ticker import Ticker
from kindred_api.turn_worker import TurnWorker
from kindred_db import create_engine, session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    base = get_settings()
    engine = create_engine(base.database_url)
    sessions = session_factory(engine)
    async with sessions() as session, session.begin():
        clock = await build_clock(base.dev_mode, session)
        await requeue_interrupted(session)
        llm = LLMRuntime(base, effective(base, await load_saved(session)))
    worker = TurnWorker(sessions, clock, llm.turn_components)
    ticker = Ticker(sessions, clock, llm.study, llm.memory)
    app.state.services = Services(
        sessions=sessions, clock=clock, worker=worker, ticker=ticker, llm=llm
    )
    tasks = [asyncio.create_task(worker.run()), asyncio.create_task(ticker.run())]
    yield
    for task in tasks:
        task.cancel()
    await engine.dispose()


app = FastAPI(title="Kindred", lifespan=lifespan)
for router in (
    health,
    dev,
    onboarding,
    chat,
    turns,
    buddy,
    progress,
    roadmap,
    notebook,
    settings,
):
    app.include_router(router.router)
