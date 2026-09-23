from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from kindred_api.chat import (
    Thread,
    post_message,
    read_reply,
    read_thread,
    to_contract,
)
from kindred_api.dependencies import ClockDep, SessionDep, WorkerDep
from kindred_api.plans import load_current_plan
from kindred_contracts import ChatMessage, MessageStatus, SendMessage
from kindred_db import Message

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages", status_code=status.HTTP_202_ACCEPTED)
async def send_message(
    body: SendMessage, session: SessionDep, clock: ClockDep, worker: WorkerDep
) -> ChatMessage:
    """Queue a message; poll its status for the stages and the audited reply."""
    plan = await load_current_plan(session)
    if plan is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "there is no plan yet")
    message = await post_message(session, plan.user_id, body.text, clock.now())
    await session.commit()
    worker.wake()
    return to_contract(message)


@router.get("/messages")
async def list_messages(
    session: SessionDep,
    clock: ClockDep,
    before_id: int | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> list[ChatMessage]:
    plan = await load_current_plan(session)
    if plan is None:
        return []
    messages = await read_thread(
        session,
        plan.user_id,
        clock.now(),
        thread=Thread.CHAT,
        before_id=before_id,
        limit=limit,
    )
    return [to_contract(message) for message in messages]


@router.get("/messages/{message_id}")
async def message_status(message_id: int, session: SessionDep) -> MessageStatus:
    message = await session.get(Message, message_id)
    if message is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    reply = await read_reply(session, message)
    return MessageStatus(
        message=to_contract(message),
        reply=to_contract(reply) if reply is not None else None,
    )
