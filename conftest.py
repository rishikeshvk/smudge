import json
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
import httpx2
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from kindred_api.auth import hash_secret
from kindred_api.clock import Clock
from kindred_api.config import get_settings
from kindred_api.dependencies import get_clock, get_session, get_worker
from kindred_api.ledger import append_note
from kindred_api.main import app
from kindred_api.schedule import plan_moment
from kindred_api.study import StudyStatus
from kindred_api.turn_worker import TurnWorker
from kindred_contracts import NoteDraft
from kindred_db import (
    EMBEDDING_DIMENSIONS,
    AuthToken,
    Buddy,
    Plan,
    StudySession,
    TopicNode,
    User,
)
from kindred_db import create_engine as create_async_engine
from kindred_llm import LLMClient

ALEMBIC_INI = Path(__file__).parent / "apps" / "api" / "alembic.ini"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def alembic_config(url: str) -> Config:
    config = Config(ALEMBIC_INI)
    config.set_main_option("sqlalchemy.url", url)
    return config


@pytest.fixture(scope="session")
def database_url() -> str:
    dev_url = make_url(get_settings().database_url)
    test_url = dev_url.set(database=f"{dev_url.database}_test")

    admin = create_engine(
        dev_url.set(database="postgres"), isolation_level="AUTOCOMMIT"
    )
    with admin.connect() as connection:
        exists = connection.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": test_url.database},
        )
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{test_url.database}"'))
    admin.dispose()

    url = test_url.render_as_string(hide_password=False)
    command.upgrade(alembic_config(url), "head")
    return url


@pytest.fixture
def migrations(database_url: str) -> Config:
    return alembic_config(database_url)


@pytest.fixture
def connection(database_url: str) -> Iterator[Connection]:
    engine = create_engine(database_url)
    with engine.connect() as connection:
        transaction = connection.begin()
        yield connection
        transaction.rollback()
    engine.dispose()


@pytest.fixture
async def sessions(
    database_url: str,
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Sessions that share one rolled-back transaction, for code that opens its own."""
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        yield async_sessionmaker(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def session(
    sessions: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sessions() as session:
        yield session


@pytest.fixture
def add_user(session: AsyncSession) -> Callable[..., Awaitable[User]]:
    async def add(*, owner: bool = False) -> User:
        user = User(timezone="UTC", is_owner=owner)
        session.add(user)
        await session.flush()
        return user

    return add


@pytest.fixture
def add_plan(session: AsyncSession) -> Callable[..., Awaitable[Plan]]:
    """A plan for a new user, or for the given one."""

    async def add(start_date: date, timezone: str, user_id: int | None = None) -> Plan:
        user = User() if user_id is None else await session.get(User, user_id)
        assert user is not None
        # A plan runs in its user's time zone.
        user.timezone = timezone
        session.add(user)
        await session.flush()
        plan = Plan(
            user_id=user.id,
            curriculum_slug="t",
            title="T",
            start_date=start_date,
            study_time=time(19),
            session_minutes=60,
            baseline_card=[],
        )
        session.add(plan)
        await session.flush()
        return plan

    return add


ScriptedLLM = Callable[[list[str]], tuple[LLMClient, list[httpx2.Request]]]


@pytest.fixture
def scripted_llm() -> ScriptedLLM:
    def build(replies: list[str]) -> tuple[LLMClient, list[httpx2.Request]]:
        seen: list[httpx2.Request] = []

        def handler(request: httpx2.Request) -> httpx2.Response:
            seen.append(request)
            return httpx2.Response(
                200,
                json={
                    "id": str(len(seen)),
                    "object": "chat.completion",
                    "created": 0,
                    "model": "scripted",
                    "choices": [
                        {
                            "index": 0,
                            "finish_reason": "stop",
                            "message": {
                                "role": "assistant",
                                "content": replies[len(seen) - 1],
                            },
                        }
                    ],
                },
            )

        client = LLMClient(
            base_url="https://llm.test/v1",
            api_key="sk-test",
            model="scripted",
            http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)),
        )
        return client, seen

    return build


@pytest.fixture
def sent_prompt() -> Callable[[httpx2.Request], tuple[str, str]]:
    def read(request: httpx2.Request) -> tuple[str, str]:
        messages = json.loads(request.content)["messages"]
        return messages[0]["content"], messages[1]["content"]

    return read


@pytest.fixture
def add_course(
    session: AsyncSession, add_plan: Callable[..., Awaitable[Plan]]
) -> Callable[..., Awaitable[Plan]]:
    """A plan from 1 Oct 2026 in Kolkata with a buddy and topics unlocking at 19:00,
    for a new user or the given one."""

    async def add(days: int, user_id: int | None = None) -> Plan:
        plan = await add_plan(date(2026, 10, 1), "Asia/Kolkata", user_id)
        session.add(Buddy(user_id=plan.user_id, name="Juno"))
        session.add_all(
            TopicNode(
                plan_id=plan.id,
                slug=f"topic-{day}",
                day=day,
                title=f"Topic {day}",
                audit_brief=f"Brief for topic {day}.",
                unlock_at=plan_moment(
                    plan.start_date, day, time(19), ZoneInfo("Asia/Kolkata")
                ),
            )
            for day in range(1, days + 1)
        )
        await session.flush()
        return plan

    return add


@pytest.fixture
def add_study(session: AsyncSession) -> Callable[..., Awaitable[None]]:
    """The buddy's study of a day's topic at a time: a note and its session, or a
    failed session."""

    async def add(
        day: int,
        at: datetime,
        *,
        failed: bool = False,
        shaky: list[str] | None = None,
        plan_id: int | None = None,
    ) -> None:
        # Without a plan, the day is looked up in the only plan there is.
        days = select(TopicNode).where(TopicNode.day == day)
        if plan_id is not None:
            days = days.where(TopicNode.plan_id == plan_id)
        [node] = await session.scalars(days)
        assert node is not None
        note_id = None
        if not failed:
            note_id = await append_note(
                session,
                node_id=node.id,
                note=NoteDraft(
                    body=f"day {day}",
                    shaky=shaky or [f"shaky {day}"],
                    sources=["https://d.t"],
                    share=f"done with topic {day}!",
                ),
                written_at=at,
                embedding=[0.5] * EMBEDDING_DIMENSIONS,
                embedding_model="fake-embed",
            )
        session.add(
            StudySession(
                node_id=node.id,
                status=(StudyStatus.FAILED if failed else StudyStatus.WRITTEN).value,
                at=at,
                note_id=note_id,
                share=None if failed else f"done with topic {day}!",
                attempts=[],
            )
        )
        await session.flush()

    return add


ApiClient = Callable[[Clock, TurnWorker | None, int | None], httpx.AsyncClient]


@pytest.fixture
async def api(session: AsyncSession) -> AsyncIterator[ApiClient]:
    """A client for the app on the test session, with the given clock and worker,
    signed in as the given user with a real token (or not signed in, for None)."""
    clients: list[httpx.AsyncClient] = []

    def connect(
        clock: Clock, worker: TurnWorker | None, user_id: int | None
    ) -> httpx.AsyncClient:
        app.dependency_overrides[get_session] = lambda: session
        app.dependency_overrides[get_clock] = lambda: clock
        if worker is not None:
            app.dependency_overrides[get_worker] = lambda: worker
        headers = {}
        if user_id is not None:
            token = f"test-token-{len(clients)}-{user_id}"
            session.add(
                AuthToken(
                    user_id=user_id,
                    token_hash=hash_secret(token),
                    created_at=clock.now(),
                )
            )
            headers["Authorization"] = f"Bearer {token}"
        client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
            headers=headers,
        )
        clients.append(client)
        return client

    yield connect
    for client in clients:
        await client.aclose()
    app.dependency_overrides.clear()
