from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.clock import OffsetClock
from kindred_api.dependencies import (
    DevClockDep,
    OwnerDep,
    SessionDep,
    TickerDep,
    get_owner,
)
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

# The dev clock is server-wide; checked first, before any other dependency.
router = APIRouter(prefix="/dev", tags=["dev"], dependencies=[Depends(get_owner)])


@router.get("/clock")
async def read_clock(
    clock: DevClockDep, session: SessionDep, owner: OwnerDep
) -> ClockView:
    return await _view(clock, session, owner.id)


@router.post("/clock")
async def change_clock(
    change: ClockChange, clock: DevClockDep, session: SessionDep, owner: OwnerDep
) -> ClockView:
    match change:
        case AdvanceClock(hours=hours):
            clock.advance(timedelta(hours=hours))
        case JumpToDay(day=day):
            plan = await load_current_plan(session, owner.id)
            if plan is None:
                raise HTTPException(status.HTTP_409_CONFLICT, "there is no plan yet")
            local_time = clock.now().astimezone(plan.tz).time()
            clock.move_to(plan_moment(plan.start_date, day, local_time, plan.tz))
        case ResetClock():
            clock.reset()
    await save_offset(session, clock.offset)
    await session.commit()
    return await _view(clock, session, owner.id)


@router.post("/study-now")
async def study_now(
    clock: DevClockDep, session: SessionDep, ticker: TickerDep, owner: OwnerDep
) -> ClockView:
    """Run tonight's study, by the owner's plan: move to the end of today's session
    if it's later, then tick everyone's plans."""
    plan = await load_current_plan(session, owner.id)
    if plan is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "there is no plan yet")
    today = max(plan_day(plan.start_date, clock.now(), plan.tz), 1)
    studied = (
        plan_moment(plan.start_date, today, plan.study_time, plan.tz)
        + plan.session_length
    )
    if clock.now() < studied:
        clock.move_to(studied)
        await save_offset(session, clock.offset)
        await session.commit()
    await ticker.tick()
    return await _view(clock, session, owner.id)


@router.post("/next-ritual")
async def next_ritual(
    clock: DevClockDep, session: SessionDep, ticker: TickerDep, owner: OwnerDep
) -> ClockView:
    """Jump to the next morning, study or night review, then tick."""
    plan = await load_current_plan(session, owner.id)
    if plan is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "there is no plan yet")
    clock.move_to(next_ritual_at(plan, ticker.rituals, clock.now()))
    await save_offset(session, clock.offset)
    await session.commit()
    await ticker.tick()
    return await _view(clock, session, owner.id)


async def _view(clock: OffsetClock, session: AsyncSession, owner_id: int) -> ClockView:
    now = clock.now()
    # The clock is global; the owner's plan gives it a day number.
    plan = await load_current_plan(session, owner_id)
    return ClockView(
        now=now,
        real_time=clock.offset == timedelta(),
        day=plan_day(plan.start_date, now, plan.tz) if plan is not None else None,
    )
