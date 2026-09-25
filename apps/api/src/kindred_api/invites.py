import secrets
from datetime import datetime, timedelta

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.auth import hash_secret, issue_token
from kindred_db import Invite

# No 0/O or 1/I, so a code read out loud or copied by hand still works.
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8


def normalise_code(raw: str) -> str:
    return "".join(char for char in raw.upper() if char.isalnum())


def display_code(code: str) -> str:
    return f"{code[:4]}-{code[4:]}"


async def create_invite(
    session: AsyncSession, user_id: int, now: datetime, valid_for: timedelta
) -> str:
    code = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
    session.add(
        Invite(
            user_id=user_id,
            code_hash=hash_secret(code),
            created_at=now,
            expires_at=now + valid_for,
        )
    )
    await session.flush()
    return display_code(code)


async def redeem(session: AsyncSession, raw_code: str, now: datetime) -> str | None:
    """A token for the invite's user; None if the code is unknown, used or expired."""
    # One statement claims the code, so two phones racing on it can't both win.
    user_id = await session.scalar(
        update(Invite)
        .where(
            Invite.code_hash == hash_secret(normalise_code(raw_code)),
            Invite.redeemed_at.is_(None),
            Invite.expires_at > now,
        )
        .values(redeemed_at=now)
        .returning(Invite.user_id)
    )
    if user_id is None:
        return None
    return await issue_token(session, user_id, now)
