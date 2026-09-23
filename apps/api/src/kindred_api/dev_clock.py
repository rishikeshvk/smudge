from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import Clock, OffsetClock, SystemClock
from kindred_db import DevClock


async def build_clock(dev_mode: bool, session: AsyncSession) -> Clock:
    if not dev_mode:
        return SystemClock()
    return OffsetClock(SystemClock(), await load_offset(session))


async def load_offset(session: AsyncSession) -> timedelta:
    row = await session.get(DevClock, 1)
    return row.offset if row is not None else timedelta()


async def save_offset(session: AsyncSession, offset: timedelta) -> None:
    await session.merge(DevClock(id=1, offset=offset))
