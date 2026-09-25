import argparse
import asyncio
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.auth import revoke
from kindred_api.config import get_settings
from kindred_api.dev_clock import build_clock
from kindred_api.invites import create_invite
from kindred_db import AuthToken, Buddy, Plan, User, create_engine, session_factory

# Onboarding sets the real time zone from the phone before anything is scheduled.
PLACEHOLDER_TIMEZONE = "UTC"


class AccountError(Exception):
    pass


async def resolve_user(session: AsyncSession, user_id: int | None) -> int:
    """The named user, or the owner, for CLIs that act as someone."""
    if user_id is not None:
        return user_id
    owner = await session.scalar(select(User.id).where(User.is_owner))
    if owner is None:
        raise AccountError("there is no owner yet; run `make seed` or `make invite`")
    return owner


async def invite(session: AsyncSession, user_id: int | None, owner: bool) -> str:
    settings = get_settings()
    # The server's clock, so a dev clock moved ahead doesn't expire the code on arrival.
    now = (await build_clock(settings.dev_mode, session)).now()
    if user_id is None:
        user = User(timezone=PLACEHOLDER_TIMEZONE, is_owner=owner)
        session.add(user)
        await session.flush()
        user_id = user.id
    elif await session.get(User, user_id) is None:
        raise AccountError(f"there is no user {user_id}")
    code = await create_invite(
        session, user_id, now, timedelta(days=settings.invite_days)
    )
    return f"{code}  for user {user_id}, works once, for {settings.invite_days} days"


async def list_users(session: AsyncSession) -> list[str]:
    tokens = (
        select(AuthToken.user_id, func.count().label("count"))
        .group_by(AuthToken.user_id)
        .subquery()
    )
    rows = await session.execute(
        select(User.id, User.is_owner, Buddy.name, Plan.start_date, tokens.c.count)
        .outerjoin(Buddy, Buddy.user_id == User.id)
        .outerjoin(Plan, Plan.user_id == User.id)
        .outerjoin(tokens, tokens.c.user_id == User.id)
        .order_by(User.id)
    )
    return [
        f"{user_id:>4}  {'owner' if is_owner else 'member':<6}  {name or '-':<10}"
        f"  {start or 'no plan'!s:<10}  {count or 0} signed in"
        for user_id, is_owner, name, start, count in rows
    ]


async def run(args: argparse.Namespace) -> None:
    engine = create_engine(get_settings().database_url)
    try:
        async with session_factory(engine)() as session, session.begin():
            if args.command == "invite":
                print(await invite(session, args.user, args.owner))
            elif args.command == "users":
                print("\n".join(await list_users(session)) or "no users yet")
            else:
                removed = await revoke(session, args.user)
                print(f"signed user {args.user} out of {removed} phone(s)")
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Invite members and manage who is signed in."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    invite_parser = commands.add_parser(
        "invite", help="mint a one-use code; a new member unless --user or --owner"
    )
    who = invite_parser.add_mutually_exclusive_group()
    who.add_argument("--user", type=int, help="a new code for this existing user")
    who.add_argument("--owner", action="store_true", help="create the server's owner")
    commands.add_parser("users", help="list users and how many phones are signed in")
    revoke_parser = commands.add_parser("revoke", help="sign a user out everywhere")
    revoke_parser.add_argument("--user", type=int, required=True)
    args = parser.parse_args()
    try:
        asyncio.run(run(args))
    except AccountError as error:
        raise SystemExit(str(error)) from error


if __name__ == "__main__":
    main()
