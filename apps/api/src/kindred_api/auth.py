import hashlib
import secrets
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_db import AuthToken, PushToken, User


def hash_secret(secret: str) -> str:
    # Tokens and codes are random, so a fast hash is enough: nothing to brute-force.
    return hashlib.sha256(secret.encode()).hexdigest()


async def issue_token(session: AsyncSession, user_id: int, now: datetime) -> str:
    token = secrets.token_urlsafe(32)
    session.add(
        AuthToken(user_id=user_id, token_hash=hash_secret(token), created_at=now)
    )
    await session.flush()
    return token


async def user_for_token(session: AsyncSession, token: str) -> User | None:
    user: User | None = await session.scalar(
        select(User)
        .join(AuthToken, AuthToken.user_id == User.id)
        .where(AuthToken.token_hash == hash_secret(token))
    )
    return user


async def sign_out(
    session: AsyncSession, user_id: int, token: str, push_token: str | None
) -> None:
    await session.execute(
        delete(AuthToken).where(AuthToken.token_hash == hash_secret(token))
    )
    if push_token is not None:
        await session.execute(
            delete(PushToken).where(
                PushToken.user_id == user_id, PushToken.token == push_token
            )
        )


async def revoke(session: AsyncSession, user_id: int) -> int:
    """Signs the user out everywhere and stops their pushes; returns tokens removed."""
    await session.execute(delete(PushToken).where(PushToken.user_id == user_id))
    removed = await session.execute(
        delete(AuthToken).where(AuthToken.user_id == user_id).returning(AuthToken.id)
    )
    return len(removed.all())
