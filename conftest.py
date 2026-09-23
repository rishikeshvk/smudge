import json
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from datetime import date, time
from pathlib import Path

import httpx2
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.config import get_settings
from kindred_db import Plan, User
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
async def session(database_url: str) -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(database_url)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        async with AsyncSession(
            bind=connection,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        ) as session:
            yield session
        await transaction.rollback()
    await engine.dispose()


@pytest.fixture
def add_plan(session: AsyncSession) -> Callable[[date, str], Awaitable[Plan]]:
    async def add(start_date: date, timezone: str) -> Plan:
        user = User(timezone=timezone)
        session.add(user)
        await session.flush()
        plan = Plan(
            user_id=user.id,
            curriculum_slug="t",
            title="T",
            start_date=start_date,
            study_time=time(19),
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
