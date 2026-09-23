import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from kindred_api.chat import requeue_interrupted
from kindred_api.config import get_settings
from kindred_api.dependencies import Services
from kindred_api.dev_clock import build_clock
from kindred_api.llm_clients import build_study_components, build_turn_components
from kindred_api.routes import (
    buddy,
    chat,
    dev,
    health,
    notebook,
    progress,
    roadmap,
    turns,
)
from kindred_api.ticker import Ticker
from kindred_api.turn_worker import TurnWorker
from kindred_db import create_engine, session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    sessions = session_factory(engine)
    async with sessions() as session, session.begin():
        clock = await build_clock(settings.dev_mode, session)
        await requeue_interrupted(session)
    worker = TurnWorker(
        sessions,
        clock,
        lambda session, plan_id, persona: build_turn_components(
            settings, session, plan_id, persona
        ),
    )
    ticker = Ticker(sessions, clock, build_study_components(settings))
    app.state.services = Services(
        sessions=sessions, clock=clock, worker=worker, ticker=ticker
    )
    tasks = [asyncio.create_task(worker.run()), asyncio.create_task(ticker.run())]
    yield
    for task in tasks:
        task.cancel()
    await engine.dispose()


app = FastAPI(title="Kindred", lifespan=lifespan)
for router in (health, dev, chat, turns, buddy, progress, roadmap, notebook):
    app.include_router(router.router)
