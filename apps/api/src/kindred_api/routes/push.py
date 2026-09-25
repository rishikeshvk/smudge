from fastapi import APIRouter, status

from kindred_api.dependencies import ClockDep, CurrentUserDep, SessionDep
from kindred_api.push import register_token
from kindred_contracts import PushRegistration

router = APIRouter(prefix="/push", tags=["push"])


@router.post("/tokens", status_code=status.HTTP_204_NO_CONTENT)
async def add_push_token(
    registration: PushRegistration,
    session: SessionDep,
    clock: ClockDep,
    user: CurrentUserDep,
) -> None:
    """A phone that should get this user's rituals; registering again is harmless."""
    await register_token(session, user.id, registration.token, clock.now())
    await session.commit()
