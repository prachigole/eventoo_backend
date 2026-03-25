import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..exceptions import BadRequest, Forbidden, NotFound
from ..models.event import Event
from ..models.task import Task, TaskStatus
from ..models.todo import TeamMember
from ..models.user import User
from ..schemas.common import ok
from ..schemas.task import TaskCreate, TaskOut, TaskUpdate
from ..services.fcm import send_push

router = APIRouter(tags=["Tasks"])

# ── Valid employee status transitions ──────────────────────────────────────────
_EMPLOYEE_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.assigned:          {TaskStatus.accepted},
    TaskStatus.accepted:          {TaskStatus.in_progress},
    TaskStatus.in_progress:       {TaskStatus.submitted},
    TaskStatus.revision_required: {TaskStatus.in_progress},
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def _owned_event(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> Event:
    event = db.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first()
    if not event:
        raise NotFound("Event")
    return event


def _validate_assignee(db: Session, manager_user: User, assignee_id: uuid.UUID) -> None:
    """Raise BadRequest if assignee_id is not a valid user.
    When the manager belongs to a company, also enforce same-company membership."""
    assignee = db.get(User, assignee_id)
    if not assignee:
        raise BadRequest("Assignee not found")
    if manager_user.company_id and assignee.company_id != manager_user.company_id:
        raise BadRequest("Assignee is not an employee in your company")


def _build_name_map(db: Session, tasks: list[Task]) -> dict[uuid.UUID, str]:
    """Return {user_id: display_name} for all assignees.

    Priority: team_member.name > users.name > users.phone > id prefix.
    """
    assignee_ids = {t.assigned_to for t in tasks if t.assigned_to}
    if not assignee_ids:
        return {}

    # First try team_member names (most human-readable, set by manager)
    members = db.query(TeamMember).filter(
        TeamMember.linked_user_id.in_(assignee_ids),
    ).all()
    name_map: dict[uuid.UUID, str] = {}
    for m in members:
        if m.linked_user_id not in name_map:
            name_map[m.linked_user_id] = m.name

    # Fall back to users.name / phone for any not covered above
    missing = assignee_ids - name_map.keys()
    if missing:
        users = db.query(User).filter(User.id.in_(missing)).all()
        for u in users:
            name_map[u.id] = u.name or u.phone or str(u.id)[:8]

    return name_map


def _serialize_tasks(
    tasks: list[Task],
    name_map: dict[uuid.UUID, str],
    event_title_map: dict[uuid.UUID, str] | None = None,
) -> list[dict]:
    result = []
    for t in tasks:
        out = TaskOut.model_validate(t)
        out.assigned_to_name = name_map.get(t.assigned_to) if t.assigned_to else None
        if event_title_map is not None:
            out.event_title = event_title_map.get(t.event_id)
        result.append(out.model_dump(by_alias=True))
    return result


def _serialize_task(task: Task, name_map: dict[uuid.UUID, str]) -> dict:
    out = TaskOut.model_validate(task)
    out.assigned_to_name = name_map.get(task.assigned_to) if task.assigned_to else None
    return out.model_dump(by_alias=True)


# ── GET /events/{event_id}/tasks ───────────────────────────────────────────────
@router.get("/events/{event_id}/tasks")
def list_tasks(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    if user.role == "manager":
        _owned_event(db, event_id, user.id)
        tasks = (
            db.query(Task)
            .filter(Task.event_id == event_id)
            .order_by(Task.sort_order, Task.created_at)
            .all()
        )
    else:
        # Employee: only their assigned tasks for this event
        tasks = (
            db.query(Task)
            .filter(Task.event_id == event_id, Task.assigned_to == user.id)
            .order_by(Task.sort_order, Task.created_at)
            .all()
        )

    name_map = _build_name_map(db, tasks)
    return ok(_serialize_tasks(tasks, name_map))


# ── POST /events/{event_id}/tasks ─────────────────────────────────────────────
@router.post("/events/{event_id}/tasks", status_code=201)
def create_task(
    event_id: uuid.UUID,
    body: TaskCreate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    if user.role != "manager":
        raise Forbidden()
    _owned_event(db, event_id, user.id)

    data = body.model_dump(by_alias=False)

    if data.get("assigned_to"):
        _validate_assignee(db, user, data["assigned_to"])

    # Auto-assign status based on whether assigned_to is set
    status = TaskStatus.assigned if data.get("assigned_to") else TaskStatus.draft

    task = Task(**data, user_id=user.id, event_id=event_id, status=status)
    db.add(task)
    db.commit()
    db.refresh(task)

    # FCM: notify the assigned employee
    if task.assigned_to:
        assignee = db.get(User, task.assigned_to)
        if assignee and assignee.fcm_token:
            send_push(
                token=assignee.fcm_token,
                title="New task assigned",
                body=task.title,
                data={"taskId": str(task.id), "eventId": str(event_id)},
            )

    name_map = _build_name_map(db, [task])
    return ok(_serialize_task(task, name_map), "Task created")


# ── PATCH /events/{event_id}/tasks/{task_id} ──────────────────────────────────
@router.patch("/events/{event_id}/tasks/{task_id}")
def update_task(
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    body: TaskUpdate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    if user.role == "manager":
        # Manager: must own the event
        _owned_event(db, event_id, user.id)
        task = db.query(Task).filter(Task.id == task_id, Task.event_id == event_id).first()
        if not task:
            raise NotFound("Task")

        updates = body.model_dump(exclude_unset=True, by_alias=False)
        new_status = updates.get("status")

        if updates.get("assigned_to"):
            _validate_assignee(db, user, updates["assigned_to"])

        # review_note may only be set when transitioning to approved or revision_required
        _REVIEW_NOTE_STATUSES = {TaskStatus.approved, TaskStatus.revision_required}
        if "review_note" in updates and new_status not in _REVIEW_NOTE_STATUSES:
            raise BadRequest("review_note can only be set when approving or requesting revision")

        for field, value in updates.items():
            setattr(task, field, value)

        db.commit()
        db.refresh(task)

        # FCM: if manager assigned/reassigned to someone, notify them
        if updates.get("assigned_to") and task.assigned_to:
            assignee = db.get(User, task.assigned_to)
            if assignee and assignee.fcm_token:
                send_push(
                    token=assignee.fcm_token,
                    title="Task assigned to you",
                    body=task.title,
                    data={"taskId": str(task.id), "eventId": str(event_id)},
                )

    else:
        # Employee: only their assigned task, only status transitions
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.event_id == event_id, Task.assigned_to == user.id)
            .first()
        )
        if not task:
            raise NotFound("Task")

        updates = body.model_dump(exclude_unset=True, by_alias=False)
        # Employees may only update status and submission_note
        allowed_fields = {"status", "submission_note"}
        non_allowed = {k for k in updates if k not in allowed_fields}
        if non_allowed:
            raise Forbidden()

        new_status = updates.get("status")
        if new_status:
            allowed = _EMPLOYEE_TRANSITIONS.get(task.status, set())
            if new_status not in allowed:
                raise BadRequest(
                    f"Cannot transition from '{task.status.value}' to '{new_status.value}'"
                )
            task.status = new_status

        # submission_note only allowed when transitioning TO submitted
        if "submission_note" in updates:
            if new_status != TaskStatus.submitted:
                raise BadRequest("submission_note can only be set when submitting")
            task.submission_note = updates["submission_note"]

        db.commit()
        db.refresh(task)

        # FCM: notify the event owner (manager) about the status change
        event = db.query(Event).filter(Event.id == event_id).first()
        if event:
            owner = db.get(User, event.user_id)
            if owner and owner.fcm_token:
                send_push(
                    token=owner.fcm_token,
                    title=f"Task update: {task.title}",
                    body=f"{user.name or user.phone or 'Employee'} → {task.status.value.replace('_', ' ')}",
                    data={"taskId": str(task.id), "eventId": str(event_id)},
                )

    name_map = _build_name_map(db, [task])
    return ok(_serialize_task(task, name_map), "Task updated")


# ── DELETE /events/{event_id}/tasks/{task_id} ─────────────────────────────────
@router.delete("/events/{event_id}/tasks/{task_id}")
def delete_task(
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    if user.role != "manager":
        raise Forbidden()
    _owned_event(db, event_id, user.id)

    task = db.query(Task).filter(Task.id == task_id, Task.event_id == event_id).first()
    if not task:
        raise NotFound("Task")
    db.delete(task)
    db.commit()
    return ok(None, "Task deleted")


# ── GET /my-tasks ─────────────────────────────────────────────────────────────
@router.get("/my-tasks")
def my_tasks(
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    tasks = (
        db.query(Task)
        .filter(Task.assigned_to == user.id)
        .order_by(Task.due_date.asc().nulls_last(), Task.created_at)
        .all()
    )
    name_map = _build_name_map(db, tasks)
    event_ids = {t.event_id for t in tasks}
    events = db.query(Event).filter(Event.id.in_(event_ids)).all() if event_ids else []
    event_title_map = {e.id: e.title for e in events}
    return ok(_serialize_tasks(tasks, name_map, event_title_map))
