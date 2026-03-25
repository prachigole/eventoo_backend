import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..exceptions import BadRequest, Forbidden, NotFound
from ..models.event import Event
from ..models.task import Task
from ..models.task_photo import TaskPhoto
from ..schemas.common import ok
from ..schemas.task_photo import TaskPhotoOut

router = APIRouter(tags=["TaskPhotos"])

# Anchored to repo root so the path is stable regardless of CWD
_BASE = Path(__file__).resolve().parents[2]
_UPLOADS = _BASE / "uploads" / "task_photos"

_ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _owned_event(db: Session, event_id: uuid.UUID, user_id: uuid.UUID) -> Event:
    event = db.query(Event).filter(Event.id == event_id, Event.user_id == user_id).first()
    if not event:
        raise NotFound("Event")
    return event


async def _save_file(file: UploadFile, task_id: uuid.UUID) -> str:
    """Saves the uploaded file and returns its API path (/uploads/...)."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_EXTS:
        raise BadRequest(f"Unsupported file type. Allowed: {', '.join(_ALLOWED_EXTS)}")

    contents = await file.read()
    if len(contents) > _MAX_FILE_SIZE:
        raise BadRequest("File too large. Maximum size is 10 MB")

    dest_dir = _UPLOADS / str(task_id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}{ext}"
    (dest_dir / filename).write_bytes(contents)

    return f"/uploads/task_photos/{task_id}/{filename}"


# ── POST /events/{event_id}/tasks/{task_id}/photos ────────────────────────────
@router.post("/events/{event_id}/tasks/{task_id}/photos", status_code=201)
async def upload_photo(
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    if user.role != "employee":
        raise Forbidden()

    task = (
        db.query(Task)
        .filter(Task.id == task_id, Task.event_id == event_id, Task.assigned_to == user.id)
        .first()
    )
    if not task:
        raise NotFound("Task")

    file_path = await _save_file(file, task_id)

    photo = TaskPhoto(
        task_id=task_id,
        event_id=event_id,
        uploaded_by=user.id,
        file_path=file_path,
        original_name=file.filename,
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return ok(TaskPhotoOut.model_validate(photo).model_dump(by_alias=True), "Photo uploaded")


# ── GET /events/{event_id}/tasks/{task_id}/photos ─────────────────────────────
@router.get("/events/{event_id}/tasks/{task_id}/photos")
def list_photos(
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    if user.role == "manager":
        _owned_event(db, event_id, user.id)
    else:
        task = (
            db.query(Task)
            .filter(Task.id == task_id, Task.event_id == event_id, Task.assigned_to == user.id)
            .first()
        )
        if not task:
            raise NotFound("Task")

    photos = (
        db.query(TaskPhoto)
        .filter(TaskPhoto.task_id == task_id, TaskPhoto.event_id == event_id)
        .order_by(TaskPhoto.created_at.desc())
        .all()
    )
    return ok([TaskPhotoOut.model_validate(p).model_dump(by_alias=True) for p in photos])


# ── DELETE /events/{event_id}/tasks/{task_id}/photos/{photo_id} ───────────────
@router.delete("/events/{event_id}/tasks/{task_id}/photos/{photo_id}")
def delete_photo(
    event_id: uuid.UUID,
    task_id: uuid.UUID,
    photo_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    photo = (
        db.query(TaskPhoto)
        .filter(
            TaskPhoto.id == photo_id,
            TaskPhoto.task_id == task_id,
            TaskPhoto.event_id == event_id,
        )
        .first()
    )
    if not photo:
        raise NotFound("Photo")

    # Manager (event owner) or the uploader can delete
    is_manager_owner = user.role == "manager" and (
        db.query(Event).filter(Event.id == event_id, Event.user_id == user.id).first()
        is not None
    )
    is_uploader = photo.uploaded_by == user.id

    if not is_manager_owner and not is_uploader:
        raise Forbidden()

    # Remove file from disk  (/uploads/task_photos/… → <repo>/uploads/task_photos/…)
    disk_path = _BASE / photo.file_path.lstrip("/")
    disk_path.unlink(missing_ok=True)

    db.delete(photo)
    db.commit()
    return ok(None, "Photo deleted")
