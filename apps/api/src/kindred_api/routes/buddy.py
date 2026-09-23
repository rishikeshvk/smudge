from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from kindred_api.dependencies import SessionDep, WorkerDep
from kindred_contracts import BuddyStatus
from kindred_db import Buddy

router = APIRouter(tags=["buddy"])


@router.get("/buddy")
async def read_buddy(session: SessionDep, worker: WorkerDep) -> BuddyStatus:
    name = await session.scalar(select(Buddy.name).order_by(Buddy.id).limit(1))
    if name is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "there is no buddy yet")
    return BuddyStatus(name=name, available=worker.available)
