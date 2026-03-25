import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..exceptions import NotFound
from ..models.event import Event
from ..models.todo import Todo, TeamMember
from ..schemas.common import ok
from ..schemas.todo import (
    TeamMemberCreate,
    TeamMemberOut,
    TodoCreate,
    TodoOut,
    TodoUpdate,
)

router = APIRouter(tags=["Todos & Team"])


def _owned_event(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> Event:
    event = db.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first()
    if not event:
        raise NotFound("Event")
    return event


# ── GET /events/{event_id}/todos ───────────────────────────────────────────────
@router.get("/events/{event_id}/todos")
def list_todos(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    _owned_event(db, event_id, user.id)
    todos = (
        db.query(Todo)
        .filter(Todo.event_id == event_id, Todo.user_id == user.id)
        .order_by(Todo.sort_order, Todo.created_at)
        .all()
    )
    return ok([TodoOut.model_validate(t).model_dump(by_alias=True) for t in todos])


# ── POST /events/{event_id}/todos ─────────────────────────────────────────────
@router.post("/events/{event_id}/todos", status_code=201)
def create_todo(
    event_id: uuid.UUID,
    body: TodoCreate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    _owned_event(db, event_id, user.id)
    todo = Todo(
        **body.model_dump(by_alias=False),
        user_id=user.id,
        event_id=event_id,
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return ok(TodoOut.model_validate(todo).model_dump(by_alias=True), "Todo created")


# ── PATCH /events/{event_id}/todos/{todo_id} ──────────────────────────────────
@router.patch("/events/{event_id}/todos/{todo_id}")
def update_todo(
    event_id: uuid.UUID,
    todo_id: str,
    body: TodoUpdate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    todo = (
        db.query(Todo)
        .filter(Todo.id == todo_id, Todo.event_id == event_id, Todo.user_id == user.id)
        .first()
    )
    if not todo:
        raise NotFound("Todo")
    for field, value in body.model_dump(exclude_unset=True, by_alias=False).items():
        setattr(todo, field, value)
    db.commit()
    db.refresh(todo)
    return ok(TodoOut.model_validate(todo).model_dump(by_alias=True), "Todo updated")


# ── DELETE /events/{event_id}/todos/{todo_id} ─────────────────────────────────
@router.delete("/events/{event_id}/todos/{todo_id}")
def delete_todo(
    event_id: uuid.UUID,
    todo_id: str,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    todo = (
        db.query(Todo)
        .filter(Todo.id == todo_id, Todo.event_id == event_id, Todo.user_id == user.id)
        .first()
    )
    if not todo:
        raise NotFound("Todo")
    db.delete(todo)
    db.commit()
    return ok(None, "Todo deleted")


# ── GET /events/{event_id}/team ───────────────────────────────────────────────
@router.get("/events/{event_id}/team")
def list_team(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    _owned_event(db, event_id, user.id)
    members = (
        db.query(TeamMember)
        .filter(TeamMember.event_id == event_id, TeamMember.user_id == user.id)
        .order_by(TeamMember.created_at)
        .all()
    )
    return ok([TeamMemberOut.model_validate(m).model_dump(by_alias=True) for m in members])


# ── POST /events/{event_id}/team ──────────────────────────────────────────────
@router.post("/events/{event_id}/team", status_code=201)
def add_team_member(
    event_id: uuid.UUID,
    body: TeamMemberCreate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    _owned_event(db, event_id, user.id)
    member = TeamMember(
        **body.model_dump(by_alias=False),
        user_id=user.id,
        event_id=event_id,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return ok(
        TeamMemberOut.model_validate(member).model_dump(by_alias=True),
        "Team member added",
    )


# ── DELETE /events/{event_id}/team/{member_id} ────────────────────────────────
@router.delete("/events/{event_id}/team/{member_id}")
def remove_team_member(
    event_id: uuid.UUID,
    member_id: str,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    member = (
        db.query(TeamMember)
        .filter(
            TeamMember.id == member_id,
            TeamMember.event_id == event_id,
            TeamMember.user_id == user.id,
        )
        .first()
    )
    if not member:
        raise NotFound("Team member")
    db.delete(member)
    db.commit()
    return ok(None, "Team member removed")
