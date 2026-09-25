import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx2
from fastapi import Depends, FastAPI
from fastapi.routing import APIRoute

from kindred_api.chat import requeue_interrupted
from kindred_api.config import get_settings
from kindred_api.dependencies import Services, get_current_user
from kindred_api.dev_clock import build_clock
from kindred_api.director import RitualSchedule
from kindred_api.llm_runtime import LLMRuntime
from kindred_api.llm_settings import effective, load_saved
from kindred_api.push import Pusher
from kindred_api.routes import (
    auth,
    buddy,
    chat,
    dev,
    health,
    notebook,
    onboarding,
    plan,
    progress,
    push,
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
    push_client = httpx2.AsyncClient(timeout=15)
    ticker = Ticker(
        sessions,
        clock,
        llm.study,
        llm.memory,
        llm.reflection,
        RitualSchedule.from_settings(base),
        Pusher(push_client, base.expo_push_url),
    )
    app.state.services = Services(
        sessions=sessions, clock=clock, worker=worker, ticker=ticker, llm=llm
    )
    tasks = [asyncio.create_task(worker.run()), asyncio.create_task(ticker.run())]
    yield
    for task in tasks:
        task.cancel()
    await push_client.aclose()
    await engine.dispose()


def operation_id(route: APIRoute) -> str:
    # The app's generated SDK names its functions after these.
    return route.name


app = FastAPI(
    title="Kindred", lifespan=lifespan, generate_unique_id_function=operation_id
)
for public in (health, auth):
    app.include_router(public.router)
# Everything else needs a signed-in user, so a route can't forget to ask for one.
for router in (
    dev,
    onboarding,
    chat,
    turns,
    buddy,
    progress,
    push,
    roadmap,
    notebook,
    plan,
    settings,
):
    app.include_router(router.router, dependencies=[Depends(get_current_user)])
