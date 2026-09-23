from datetime import timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import OffsetClock, SystemClock
from kindred_api.dev_clock import build_clock, load_offset, save_offset


@pytest.mark.anyio
async def test_offset_is_zero_until_saved(session: AsyncSession) -> None:
    assert await load_offset(session) == timedelta()


@pytest.mark.anyio
async def test_saved_offset_replaces_the_last_one(session: AsyncSession) -> None:
    await save_offset(session, timedelta(days=3))
    await save_offset(session, timedelta(hours=5))

    assert await load_offset(session) == timedelta(hours=5)


@pytest.mark.anyio
async def test_dev_mode_resumes_the_saved_offset(session: AsyncSession) -> None:
    await save_offset(session, timedelta(days=8))

    clock = await build_clock(True, session)

    assert isinstance(clock, OffsetClock)
    assert clock.offset == timedelta(days=8)


@pytest.mark.anyio
async def test_real_time_outside_dev_mode(session: AsyncSession) -> None:
    await save_offset(session, timedelta(days=8))

    assert isinstance(await build_clock(False, session), SystemClock)
