# Architecture

## Folder Structure

```
eventoo_backend/
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI app, CORS middleware, exception handlers, router includes
│   ├── config.py           # Pydantic Settings — reads .env for DATABASE_URL, DEV_SKIP_AUTH, etc.
│   ├── database.py         # SQLAlchemy engine, SessionLocal, get_db(), in-process user cache
│   ├── auth.py             # Firebase JWT verification, DEV_SKIP_AUTH mode, TokenData model
│   ├── exceptions.py       # AppException, NotFound, Forbidden, Conflict, BadRequest + handler
│   ├── logging_middleware.py  # RequestLoggingMiddleware — logs method, path, status, duration
│   ├── mdns.py             # Zeroconf mDNS advertisement (_eventoo._tcp.local.)
│   ├── models/
│   │   ├── __init__.py     # Re-exports Base and all models so Alembic sees them
│   │   ├── base.py         # SQLAlchemy DeclarativeBase
│   │   ├── user.py         # User (firebase_uid, role, client_event_id)
│   │   ├── event.py        # Event + EventCategory/EventStatus enums
│   │   ├── vendor.py       # Vendor + VendorCategory enum
│   │   ├── candidate.py    # Candidate (event shortlist) + CandidateStatus enum
│   │   ├── todo.py         # Todo (per-event checklist item)
│   │   ├── invite.py       # InviteToken (employee onboarding)
│   │   ├── task.py         # Task + TaskStatus/TaskPriority enums
│   │   ├── extension_request.py  # ExtensionRequest + ExtReqStatus enum
│   │   ├── task_photo.py   # TaskPhoto (uploaded evidence files)
│   │   └── client_invite.py      # ClientInviteToken (client portal access)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── events.py          # GET/POST/PATCH/DELETE /api/v1/events
│   │   ├── vendors.py         # GET/POST/PATCH/DELETE /api/v1/vendors
│   │   ├── candidates.py      # GET/POST/PATCH/DELETE /api/v1/events/{id}/candidates
│   │   ├── todos.py           # GET/POST/PATCH/DELETE /api/v1/events/{id}/todos
│   │   ├── users.py           # GET /api/v1/me
│   │   ├── invites.py         # POST /api/v1/invites, POST /api/v1/invites/accept
│   │   ├── tasks.py           # CRUD /api/v1/events/{id}/tasks, GET /api/v1/my-tasks
│   │   ├── extension_requests.py  # CRUD /api/v1/events/{id}/tasks/{id}/extension-requests
│   │   ├── task_photos.py     # POST/GET/DELETE /api/v1/events/{id}/tasks/{id}/photos
│   │   └── client_invites.py  # Client portal invite + portal data endpoints
│   └── schemas/
│       ├── common.py          # CamelSchema base, ApiResponse, ok(), paginated() helpers
│       ├── event.py           # EventCreate, EventUpdate, EventSummary, EventDetail
│       ├── vendor.py          # VendorCreate, VendorUpdate, VendorSummary, VendorDetail
│       ├── candidate.py       # CandidateCreate, CandidateUpdate, CandidateWithVendor
│       ├── task.py            # TaskCreate, TaskUpdate, TaskOut
│       ├── extension_request.py  # ExtensionRequestCreate, ExtensionRequestOut, ReviewBody
│       ├── task_photo.py      # TaskPhotoOut
│       └── client_invite.py   # ClientInviteOut, ClientPortalData, ApprovedTask
├── alembic/
│   ├── env.py              # Alembic migration environment
│   ├── alembic.ini
│   └── versions/
│       ├── 0001_initial.py
│       ├── 0002_add_vendor_ids_todos_team.py
│       ├── 0003_add_user_role.py
│       ├── 0004_add_invite_tokens.py
│       ├── 0005_add_tasks.py
│       ├── 0006_add_extension_requests.py
│       ├── 0007_add_task_photos.py
│       ├── 0008_add_task_submission_fields.py
│       └── 0009_add_client_portal.py
├── tests/
│   ├── conftest.py              # SQLite test DB, TestClient, auth_headers fixtures
│   ├── test_health.py
│   ├── test_events.py
│   ├── test_vendors.py
│   ├── test_candidates.py
│   ├── test_security.py
│   ├── test_task_submission.py
│   ├── test_extension_requests.py
│   ├── test_task_photos.py
│   └── test_client_portal.py
├── uploads/                # Task photo files (not committed)
│   └── task_photos/
├── docs/                   # This documentation
├── scripts/
│   ├── pre-commit-validate.sh
│   └── update-test-docs.sh
├── start.sh                # Activate venv + start Uvicorn
├── requirements.txt
├── .gitignore
├── .env.example
└── CONTRIBUTING.md
```

---

## Request Lifecycle

```
HTTP Request
    │
    ▼
CORSMiddleware (allow_origins=["*"])
    │
    ▼
Router function
    │
    ├── verify_token(authorization: Header)
    │       ├── DEV_SKIP_AUTH=true → _decode_jwt_payload() — no sig verification
    │       │       uid = payload.user_id or sub or uid or raw token string
    │       └── DEV_SKIP_AUTH=false → Firebase Admin SDK verify_id_token()
    │       Returns TokenData(uid, phone)
    │
    ├── get_or_create_user(db, uid, phone)
    │       ├── Check in-process cache _uid_to_user_id dict
    │       ├── Cache miss → db.query(User).filter(firebase_uid==uid).first()
    │       └── Not found → INSERT + commit
    │       Returns User row
    │
    ├── Business logic (query DB, validate ownership)
    │       └── NotFound / Conflict / Forbidden → raises AppException
    │
    ├── Pydantic schema validation (model_validate + model_dump(by_alias=True))
    │
    └── ok() or paginated() → dict response
            {"success": true, "data": {...}, "message": "..."}
```

---

## Auth Flow

1. Flutter app calls `FirebaseAuth.instance.currentUser.getIdToken()` — auto-refreshes on expiry.
2. Dio interceptor in `api_client.dart` sets `Authorization: Bearer <token>` on every request.
3. `verify_token` FastAPI dependency extracts the header.
4. **DEV mode** (`DEV_SKIP_AUTH=true`): JWT payload decoded locally without signature check. `uid` taken from `user_id`, `sub`, or `uid` claim in that order; falls back to the raw token string.
5. **Production** (`DEV_SKIP_AUTH=false`): Firebase Admin SDK `auth.verify_id_token()` called with the live Firebase app initialized from `firebase_credentials_path`.
6. `get_or_create_user()` upserts the user row keyed on `firebase_uid`, then caches the mapping `firebase_uid → internal UUID` in-process to skip DB lookups on subsequent requests in the same process lifetime.

---

## Environment Variables

Loaded from `.env` via pydantic-settings `SettingsConfigDict`.

| Variable | Type | Required | Default | Description |
|---|---|---|---|---|
| `DATABASE_URL` | string | Yes | — | SQLAlchemy-format PostgreSQL URL, e.g. `postgresql://user:pw@localhost:5432/eventoo` |
| `FIREBASE_CREDENTIALS_PATH` | string | No | `""` | Path to Firebase service account JSON. Only needed when `DEV_SKIP_AUTH=false` |
| `DEV_SKIP_AUTH` | bool | No | `false` | Skip Firebase JWT signature verification. **Never true in production.** |

---

## Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "Event not found"
  }
}
```

Error codes used:

| Code | HTTP Status | Source |
|---|---|---|
| `UNAUTHORIZED` | 401 | Missing/invalid Authorization header or token |
| `FORBIDDEN` | 403 | Resource exists but caller does not own it |
| `NOT_FOUND` | 404 | Resource does not exist (or not owned — no info leakage) |
| `CONFLICT` | 409 | Duplicate shortlisting |
| `BAD_REQUEST` | 400 | Semantic error (future use) |
| `VALIDATION_ERROR` | 422 | Pydantic validation failure — first error surfaced |
| `INTERNAL_ERROR` | 500 | Unhandled exception |

---

## Success Response Format

Single object:
```json
{"success": true, "data": {...}, "message": "Event created"}
```

List (paginated):
```json
{
  "success": true,
  "data": {
    "items": [...],
    "meta": {"total": 42, "page": 1, "perPage": 50, "totalPages": 1}
  }
}
```

Candidate list is returned as a plain array (not paginated) via `ok([...])`:
```json
{"success": true, "data": [...], "message": null}
```

---

## camelCase JSON

All schemas inherit `CamelSchema` which sets `alias_generator=to_camel` from pydantic. This means:
- Python field `attendee_count` → JSON key `attendeeCount`
- Python field `price_range` → JSON key `priceRange`
- Both camelCase and snake_case are accepted on input (`populate_by_name=True`)
