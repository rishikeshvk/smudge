from fastapi import APIRouter, HTTPException, status

from kindred_api.dependencies import SessionDep
from kindred_contracts import TurnTrace
from kindred_db import Turn

router = APIRouter(prefix="/turns", tags=["turns"])


@router.get("/{turn_id}")
async def read_turn(turn_id: int, session: SessionDep) -> TurnTrace:
    """The full trace behind one buddy reply, for the X-ray view."""
    turn = await session.get(Turn, turn_id)
    if turn is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return TurnTrace.model_validate(turn.trace)
