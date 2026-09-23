from sqlalchemy.ext.asyncio import AsyncSession

from kindred_contracts import TurnTrace
from kindred_db import Turn


async def record_turn(
    session: AsyncSession,
    trace: TurnTrace,
    *,
    plan_id: int,
    session_id: str,
    probe_run_id: str | None = None,
) -> None:
    session.add(
        Turn(
            plan_id=plan_id,
            session_id=session_id,
            probe_run_id=probe_run_id,
            at=trace.at,
            message=trace.message,
            route=trace.directive.route.value,
            fell_back=trace.fell_back,
            final_reply=trace.final_reply,
            trace=trace.model_dump(mode="json"),
        )
    )
    await session.flush()
