from fastapi import APIRouter, HTTPException, status

from kindred_api.dependencies import ClockDep, CurrentUserDep, SessionDep
from kindred_api.plans import load_current_plan
from kindred_contracts import NotebookNote, NotebookView, SealedDay
from kindred_gate import list_notes, load_topic_map

router = APIRouter(prefix="/notebook", tags=["notebook"])


@router.get("")
async def read_notebook(
    session: SessionDep, clock: ClockDep, user: CurrentUserDep
) -> NotebookView:
    plan = await load_current_plan(session, user.id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "there is no plan yet")
    now = clock.now()
    notes = await list_notes(session, plan_id=plan.id, now=now)
    written = {note.topic.day for note in notes}
    topics = await load_topic_map(session, plan.id)
    return NotebookView(
        notes=notes,
        sealed=[
            SealedDay(day=topic.day, unlocks_at=topic.unlock_at)
            for topic in topics.topics
            if topic.day not in written
        ],
    )


@router.get("/{note_id}")
async def read_note(
    note_id: int, session: SessionDep, clock: ClockDep, user: CurrentUserDep
) -> NotebookNote:
    plan = await load_current_plan(session, user.id)
    notes = (
        await list_notes(session, plan_id=plan.id, now=clock.now())
        if plan is not None
        else []
    )
    # A note that isn't visible yet, or isn't this user's, is as absent as one that
    # doesn't exist.
    found = next((note for note in notes if note.note_id == note_id), None)
    if found is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    return found
