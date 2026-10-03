from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.auth import user_for_token
from kindred_api.clock import Clock, OffsetClock
from kindred_api.demo import DemoBudget
from kindred_api.ingest import SourceFetcher
from kindred_api.llm_runtime import LLMRuntime
from kindred_api.onboarding import Planning
from kindred_api.ticker import Ticker
from kindred_api.turn_worker import TurnWorker
from kindred_db import User


@dataclass(frozen=True)
class Services:
    sessions: async_sessionmaker[AsyncSession]
    clock: Clock
    worker: TurnWorker
    ticker: Ticker
    llm: LLMRuntime
    sources: SourceFetcher
    demo: DemoBudget


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


def get_sources(services: Annotated[Services, Depends(get_services)]) -> SourceFetcher:
    return services.sources


def get_llm(services: Annotated[Services, Depends(get_services)]) -> LLMRuntime:
    return services.llm


def get_demo_budget(services: Annotated[Services, Depends(get_services)]) -> DemoBudget:
    return services.demo


def get_planning(llm: Annotated[LLMRuntime, Depends(get_llm)]) -> Planning:
    return llm.planning()


def get_dev_clock(clock: Annotated[Clock, Depends(get_clock)]) -> OffsetClock:
    # Outside dev mode the API runs on real time and has no time controls at all.
    if not isinstance(clock, OffsetClock):
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return clock


bearer = HTTPBearer(auto_error=False)


def unauthorized() -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "sign in with an invite code",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    if credentials is None:
        raise unauthorized()
    return credentials.credentials


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    token: Annotated[str, Depends(get_token)],
) -> User:
    """The signed-in user: the only source of who is asking (invariant 8)."""
    user = await user_for_token(session, token)
    if user is None:
        raise unauthorized()
    return user


def get_owner(user: Annotated[User, Depends(get_current_user)]) -> User:
    # LLM settings and the dev clock are server-wide, so only the owner touches them.
    if not user.is_owner:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "only the owner can do that")
    return user


SessionDep = Annotated[AsyncSession, Depends(get_session)]
TokenDep = Annotated[str, Depends(get_token)]
CurrentUserDep = Annotated[User, Depends(get_current_user)]
OwnerDep = Annotated[User, Depends(get_owner)]
ClockDep = Annotated[Clock, Depends(get_clock)]
DevClockDep = Annotated[OffsetClock, Depends(get_dev_clock)]
WorkerDep = Annotated[TurnWorker, Depends(get_worker)]
TickerDep = Annotated[Ticker, Depends(get_ticker)]
PlanningDep = Annotated[Planning, Depends(get_planning)]
LLMRuntimeDep = Annotated[LLMRuntime, Depends(get_llm)]
SourcesDep = Annotated[SourceFetcher, Depends(get_sources)]
DemoBudgetDep = Annotated[DemoBudget, Depends(get_demo_budget)]
