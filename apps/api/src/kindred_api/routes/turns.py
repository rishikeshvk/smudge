from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from kindred_api.dependencies import CurrentUserDep, SessionDep
from kindred_contracts import TurnTrace
from kindred_db import Plan, Turn

router = APIRouter(prefix="/turns", tags=["turns"])


@router.get("/{turn_id}")
async def read_turn(
    turn_id: int, session: SessionDep, user: CurrentUserDep
) -> TurnTrace:
    """The full trace behind one buddy reply, for the X-ray view."""
    turn = await session.scalar(
        select(Turn)
        .join(Plan, Turn.plan_id == Plan.id)
        .where(Turn.id == turn_id, Plan.user_id == user.id)
    )
    if turn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return TurnTrace.model_validate(turn.trace)
