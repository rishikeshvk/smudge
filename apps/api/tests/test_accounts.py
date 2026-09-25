from datetime import date, time

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kindred_api.accounts import AccountError, invite, list_users
from kindred_db import Buddy, Invite, Plan, User


@pytest.mark.anyio
async def test_an_invite_makes_a_new_member(session: AsyncSession) -> None:
    line = await invite(session, None, owner=False)

    user = await session.scalar(select(User))
    assert user is not None and not user.is_owner
    assert f"for user {user.id}" in line
    assert await session.scalar(select(Invite.user_id)) == user.id


@pytest.mark.anyio
async def test_an_invite_for_an_existing_user_makes_no_one_new(
    session: AsyncSession,
) -> None:
    user = User(timezone="Asia/Kolkata")
    session.add(user)
    await session.flush()

    await invite(session, user.id, owner=False)

    assert list(await session.scalars(select(User.id))) == [user.id]


@pytest.mark.anyio
async def test_an_invite_for_a_missing_user_is_refused(session: AsyncSession) -> None:
    with pytest.raises(AccountError):
        await invite(session, 999_999, owner=False)


@pytest.mark.anyio
async def test_the_list_shows_who_has_a_buddy_and_a_plan(
    session: AsyncSession,
) -> None:
    await invite(session, None, owner=True)
    owner = await session.scalar(select(User).where(User.is_owner))
    assert owner is not None
    session.add(Buddy(user_id=owner.id, name="Juno"))
    session.add(
        Plan(
            user_id=owner.id,
            curriculum_slug="t",
            title="T",
            start_date=date(2026, 10, 1),
            study_time=time(19),
            baseline_card=[],
        )
    )
    await invite(session, None, owner=False)
    await session.flush()

    lines = await list_users(session)

    assert "owner" in lines[0] and "Juno" in lines[0] and "2026-10-01" in lines[0]
    assert "member" in lines[1] and "no plan" in lines[1]
