from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.clock import Clock, OffsetClock
from kindred_api.llm_runtime import LLMRuntime
from kindred_api.onboarding import Planning
from kindred_api.ticker import Ticker
from kindred_api.turn_worker import TurnWorker


@dataclass(frozen=True)
class Services:
    sessions: async_sessionmaker[AsyncSession]
    clock: Clock
    worker: TurnWorker
    ticker: Ticker
    llm: LLMRuntime


def get_services(request: Request) -> Services:
    services: Services = request.app.state.services
    return services


async def get_session(
    services: Annotated[Services, Depends(get_services)],
) -> AsyncIterator[AsyncSession]:
    async with services.sessions() as session:
        yield session


def get_clock(services: Annotated[Services, Depends(get_services)]) -> Clock:
    return services.clock


def get_worker(services: Annotated[Services, Depends(get_services)]) -> TurnWorker:
    return services.worker


def get_ticker(services: Annotated[Services, Depends(get_services)]) -> Ticker:
    return services.ticker


def get_llm(services: Annotated[Services, Depends(get_services)]) -> LLMRuntime:
    return services.llm


def get_planning(llm: Annotated[LLMRuntime, Depends(get_llm)]) -> Planning:
    return llm.planning()


def get_dev_clock(clock: Annotated[Clock, Depends(get_clock)]) -> OffsetClock:
    # Outside dev mode the API runs on real time and has no time controls at all.
    if not isinstance(clock, OffsetClock):
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return clock


SessionDep = Annotated[AsyncSession, Depends(get_session)]
ClockDep = Annotated[Clock, Depends(get_clock)]
DevClockDep = Annotated[OffsetClock, Depends(get_dev_clock)]
WorkerDep = Annotated[TurnWorker, Depends(get_worker)]
TickerDep = Annotated[Ticker, Depends(get_ticker)]
PlanningDep = Annotated[Planning, Depends(get_planning)]
LLMRuntimeDep = Annotated[LLMRuntime, Depends(get_llm)]
