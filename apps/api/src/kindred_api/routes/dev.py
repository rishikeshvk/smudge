from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import OffsetClock
from kindred_api.dependencies import DevClockDep, SessionDep, TickerDep
from kindred_api.dev_clock import save_offset
from kindred_api.director import next_ritual_at
from kindred_api.plans import load_current_plan
from kindred_api.schedule import plan_day, plan_moment
from kindred_contracts import (
    AdvanceClock,
    ClockChange,
    ClockView,
    JumpToDay,
    ResetClock,
)

router = APIRouter(prefix="/dev", tags=["dev"])


@router.get("/clock")
async def read_clock(clock: DevClockDep, session: SessionDep) -> ClockView:
    return await _view(clock, session)


@router.post("/clock")
async def change_clock(
    change: ClockChange, clock: DevClockDep, session: SessionDep
) -> ClockView:
    match change:
        case AdvanceClock(hours=hours):
            clock.advance(timedelta(hours=hours))
        case JumpToDay(day=day):
            plan = await load_current_plan(session)
            if plan is None:
                raise HTTPException(status.HTTP_409_CONFLICT, "there is no plan yet")
            local_time = clock.now().astimezone(plan.tz).time()
            clock.move_to(plan_moment(plan.start_date, day, local_time, plan.tz))
        case ResetClock():
            clock.reset()
    await save_offset(session, clock.offset)
    await session.commit()
    return await _view(clock, session)


@router.post("/study-now")
async def study_now(
    clock: DevClockDep, session: SessionDep, ticker: TickerDep
) -> ClockView:
    """Run tonight's study: move to today's study time if it's earlier, then tick."""
    plan = await load_current_plan(session)
    if plan is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "there is no plan yet")
    today = max(plan_day(plan.start_date, clock.now(), plan.tz), 1)
    tonight = plan_moment(plan.start_date, today, plan.study_time, plan.tz)
    if clock.now() < tonight:
        clock.move_to(tonight)
        await save_offset(session, clock.offset)
        await session.commit()
    await ticker.tick()
    return await _view(clock, session)


@router.post("/next-ritual")
async def next_ritual(
    clock: DevClockDep, session: SessionDep, ticker: TickerDep
) -> ClockView:
    """Jump to the next morning, study or night review, then tick."""
    plan = await load_current_plan(session)
    if plan is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "there is no plan yet")
    clock.move_to(next_ritual_at(plan, ticker.rituals, clock.now()))
    await save_offset(session, clock.offset)
    await session.commit()
    await ticker.tick()
    return await _view(clock, session)


async def _view(clock: OffsetClock, session: AsyncSession) -> ClockView:
    now = clock.now()
    plan = await load_current_plan(session)
    return ClockView(
        now=now,
        real_time=clock.offset == timedelta(),
        day=plan_day(plan.start_date, now, plan.tz) if plan is not None else None,
    )
