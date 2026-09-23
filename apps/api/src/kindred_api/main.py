from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from kindred_api.config import get_settings
from kindred_api.dependencies import Services
from kindred_api.dev_clock import build_clock
from kindred_api.routes import dev, health
from kindred_db import create_engine, session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    sessions = session_factory(engine)
    async with sessions() as session:
        clock = await build_clock(settings.dev_mode, session)
    app.state.services = Services(sessions=sessions, clock=clock)
    yield
    await engine.dispose()


app = FastAPI(title="Kindred", lifespan=lifespan)
app.include_router(health.router)
app.include_router(dev.router)
