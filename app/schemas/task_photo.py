import uuid
from datetime import datetime

from .common import CamelSchema


class TaskPhotoOut(CamelSchema):
    id: uuid.UUID
    task_id: uuid.UUID
    event_id: uuid.UUID
    uploaded_by: uuid.UUID
    file_path: str
    original_name: str | None
    created_at: datetime
