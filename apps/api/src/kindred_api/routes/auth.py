from fastapi import APIRouter, HTTPException, status

from kindred_api import auth
from kindred_api.dependencies import ClockDep, CurrentUserDep, SessionDep, TokenDep
from kindred_api.invites import redeem
from kindred_contracts import AuthToken, Me, RedeemInvite, SignOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/redeem")
async def redeem_invite(
    body: RedeemInvite, session: SessionDep, clock: ClockDep
) -> AuthToken:
    """Trade a one-use invite code for this phone's token."""
    token = await redeem(session, body.code, clock.now())
    if token is None:
        # Unknown, used and expired look the same, so a guess learns nothing.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "that code doesn't work")
    await session.commit()
    return AuthToken(token=token)


@router.get("/me")
async def read_me(user: CurrentUserDep) -> Me:
    return Me(is_owner=user.is_owner)


@router.post("/sign-out", status_code=status.HTTP_204_NO_CONTENT)
async def sign_out(
    body: SignOut, session: SessionDep, user: CurrentUserDep, token: TokenDep
) -> None:
    """End this phone's session and stop its pushes."""
    await auth.sign_out(session, user.id, token, body.push_token)
    await session.commit()
