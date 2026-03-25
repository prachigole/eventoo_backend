# Test Cases — Eventoo Backend

Master test plan for the pytest test suite.

## Running Tests

```bash
cd eventoo_backend
source .venv/bin/activate
python -m pytest tests/ -v --tb=short
```

- `--tb=short` prints the failing test name and the exact assertion that failed.
- A passing run ends with `X passed` and no red output.
- Any test that does not pass must be fixed before merging.

## Coverage Rule

Every API endpoint must have test cases for **all three response types**:

| Type | Example |
|---|---|
| **Empty** | List with no records returns `data: []`; GET unknown ID returns 404 |
| **Success** | Valid input returns the expected HTTP status and response shape |
| **Error** | Invalid/missing field returns 4xx with `success: false` |

---

## Health

| ID | Test | File | Expected | Status |
|---|---|---|---|---|
| HEALTH-001 | Health endpoint returns `{"status": "ok"}` | test_health.py | 200 OK | ✅ Pass |

---

## Events

| ID | Test | File | Expected | Status |
|---|---|---|---|---|
| EVENT-001 | List events (empty) — authenticated user with no events | test_events.py | 200, items=[] | ✅ Pass |
| EVENT-002 | Create event with valid data | test_events.py | 201, event in response | ✅ Pass |
| EVENT-003 | Create event missing required field (title) | test_events.py | 422 | ✅ Pass |
| EVENT-004 | Create event with invalid category value | test_events.py | 422 | ✅ Pass |
| EVENT-005 | Get event by id | test_events.py | 200, correct event | ✅ Pass |
| EVENT-006 | Get non-existent event | test_events.py | 404 | ✅ Pass |
| EVENT-007 | Update event via PATCH | test_events.py | 200, updated field reflected | ✅ Pass |
| EVENT-008 | Update event with wrong UUID (not owned) | test_events.py | 404 | ✅ Pass |
| EVENT-009 | Delete event, then list shows empty | test_events.py | 200 delete, then 200 with items=[] | ✅ Pass |
| EVENT-010 | List events with status filter | test_events.py | 200, only matching status | ✅ Pass |
| EVENT-011 | List events with search filter | test_events.py | 200, only matching title | ✅ Pass |
| EVENT-012 | No auth header on protected endpoint | test_events.py | 401 | ✅ Pass |
| EVENT-013 | Create then list — created event appears in list | test_events.py | 200, items length=1 | ✅ Pass |

---

## Vendors

| ID | Test | File | Expected | Status |
|---|---|---|---|---|
| VENDOR-001 | List vendors (empty) | test_vendors.py | 200, items=[] | ✅ Pass |
| VENDOR-002 | Create vendor with valid data | test_vendors.py | 201, vendor in response | ✅ Pass |
| VENDOR-003 | Create vendor missing required field (name) | test_vendors.py | 422 | ✅ Pass |
| VENDOR-004 | Get vendor by id | test_vendors.py | 200, correct vendor | ✅ Pass |
| VENDOR-005 | Get non-existent vendor | test_vendors.py | 404 | ✅ Pass |
| VENDOR-006 | Update vendor via PATCH | test_vendors.py | 200, updated field reflected | ✅ Pass |
| VENDOR-007 | Delete vendor | test_vendors.py | 200 delete, then 404 on GET | ✅ Pass |
| VENDOR-008 | List vendors with category filter | test_vendors.py | 200, only matching category | ✅ Pass |
| VENDOR-009 | List vendors with search filter | test_vendors.py | 200, only matching name | ✅ Pass |
| VENDOR-010 | List vendors with min_rating filter | test_vendors.py | 200, only vendors above threshold | ✅ Pass |
| VENDOR-011 | No auth header | test_vendors.py | 401 | ✅ Pass |

---

## Candidates

| ID | Test | File | Expected | Status |
|---|---|---|---|---|
| CAND-001 | List candidates for event (empty) | test_candidates.py | 200, data=[] | ✅ Pass |
| CAND-002 | Add vendor to event shortlist | test_candidates.py | 201, candidate with vendor data | ✅ Pass |
| CAND-003 | Add same vendor twice — conflict | test_candidates.py | 409 | ✅ Pass |
| CAND-004 | Add vendor not owned by user — 404 | test_candidates.py | 404 | ✅ Pass |
| CAND-005 | Update candidate quoted_cost and status | test_candidates.py | 200, updated fields | ✅ Pass |
| CAND-006 | Remove candidate from shortlist | test_candidates.py | 200, then list shows empty | ✅ Pass |
| CAND-007 | List candidates shows nested vendor data | test_candidates.py | 200, data[0].vendor exists | ✅ Pass |
| CAND-008 | Candidates for non-existent event | test_candidates.py | 404 | ✅ Pass |

---

## Security

| ID | Test | File | Expected | Status |
|---|---|---|---|---|
| SEC-001 | No auth token on events endpoint | test_security.py | 401 | ✅ Pass |
| SEC-002 | Malformed token (no "Bearer " prefix) | test_security.py | 401 | ✅ Pass |
| SEC-003 | IDOR — user A cannot read user B's events | test_security.py | 200 for A, 404 for B | ✅ Pass |
| SEC-004 | SQL injection in search param | test_security.py | 200, no crash | ✅ Pass |
| SEC-005 | Title over 255 chars | test_security.py | 422 | ✅ Pass |

---

## Users & Invites

| ID | Test | File | Expected | Status |
|---|---|---|---|---|
| USER-001 | GET /me returns current user with role | test_users.py | 200, role=manager | ⬜ Todo |
| USER-002 | GET /me with no prior record auto-creates user | test_users.py | 200, user created | ⬜ Todo |
| INVITE-001 | POST /invites — manager creates invite token | test_invites.py | 201, token in response | ⬜ Todo |
| INVITE-002 | POST /invites/accept — valid token sets role=employee | test_invites.py | 200, role updated | ⬜ Todo |
| INVITE-003 | POST /invites/accept — already-used token returns error | test_invites.py | 400 | ⬜ Todo |
| INVITE-004 | POST /invites/accept — non-existent token returns 404 | test_invites.py | 404 | ⬜ Todo |

---

## Tasks

| ID | Test | File | Expected | Status |
|---|---|---|---|---|
| TASK-001 | List tasks for event (empty) | test_tasks.py | 200, data=[] | ⬜ Todo |
| TASK-002 | Manager creates task with valid data | test_tasks.py | 201, task in response | ⬜ Todo |
| TASK-003 | Manager creates task missing required field | test_tasks.py | 422 | ⬜ Todo |
| TASK-004 | Employee cannot create task | test_tasks.py | 403 | ⬜ Todo |
| TASK-005 | Manager updates task title via PATCH | test_tasks.py | 200, updated field reflected | ⬜ Todo |
| TASK-006 | Manager sets review_note when approving | test_tasks.py | 200, review_note saved | ⬜ Todo |
| TASK-007 | Manager setting review_note without status change returns error | test_tasks.py | 400 | ⬜ Todo |
| TASK-008 | Employee transitions status along valid path | test_tasks.py | 200, status updated | ⬜ Todo |
| TASK-009 | Employee invalid status transition returns error | test_tasks.py | 400 | ⬜ Todo |
| TASK-010 | Employee cannot set review_note | test_tasks.py | 403 | ⬜ Todo |
| TASK-011 | Employee sets submission_note when transitioning to submitted | test_tasks.py | 200, note saved | ⬜ Todo |
| TASK-012 | Employee setting submission_note without submitting returns error | test_tasks.py | 400 | ⬜ Todo |
| TASK-013 | Manager deletes task | test_tasks.py | 200, then 404 on re-fetch | ⬜ Todo |
| TASK-014 | GET /my-tasks returns only tasks assigned to current user | test_tasks.py | 200, correct tasks | ⬜ Todo |

---

## Extension Requests

| ID | Test | File | Expected | Status |
|---|---|---|---|---|
| EXT-001 | List extension requests for task (empty) | test_extension_requests.py | 200, data=[] | ⬜ Todo |
| EXT-002 | Employee submits valid extension request | test_extension_requests.py | 201, request in response | ⬜ Todo |
| EXT-003 | Employee submits request missing new_due_date | test_extension_requests.py | 422 | ⬜ Todo |
| EXT-004 | Manager cannot submit extension request | test_extension_requests.py | 403 | ⬜ Todo |
| EXT-005 | Manager approves extension request | test_extension_requests.py | 200, status=approved | ⬜ Todo |
| EXT-006 | Manager rejects extension request | test_extension_requests.py | 200, status=rejected | ⬜ Todo |
| EXT-007 | Non-owner cannot approve request | test_extension_requests.py | 403/404 | ⬜ Todo |

---

## Task Photos

| ID | Test | File | Expected | Status |
|---|---|---|---|---|
| PHOTO-001 | List photos for task (empty) | test_task_photos.py | 200, data=[] | ⬜ Todo |
| PHOTO-002 | Employee uploads valid photo | test_task_photos.py | 201, file_path in response | ⬜ Todo |
| PHOTO-003 | Upload rejected for unsupported extension | test_task_photos.py | 400 | ⬜ Todo |
| PHOTO-004 | Upload rejected when file exceeds 10 MB | test_task_photos.py | 400 | ⬜ Todo |
| PHOTO-005 | Manager cannot upload (only employees can) | test_task_photos.py | 403 | ⬜ Todo |
| PHOTO-006 | Manager views photos for their task | test_task_photos.py | 200, list of photos | ⬜ Todo |
| PHOTO-007 | Delete photo removes DB record | test_task_photos.py | 200, then 404 | ⬜ Todo |
| PHOTO-008 | Non-owner/non-uploader cannot delete | test_task_photos.py | 403 | ⬜ Todo |

---

## Client Portal

| ID | Test | File | Expected | Status |
|---|---|---|---|---|
| CLIENT-001 | Manager creates client invite | test_client_portal.py | 201, token in response | ⬜ Todo |
| CLIENT-002 | Non-manager cannot create invite | test_client_portal.py | 403 | ⬜ Todo |
| CLIENT-003 | Client redeems valid invite token | test_client_portal.py | 200, role=client | ⬜ Todo |
| CLIENT-004 | Redeeming already-used token returns error | test_client_portal.py | 400 | ⬜ Todo |
| CLIENT-005 | Redeeming non-existent token returns 404 | test_client_portal.py | 404 | ⬜ Todo |
| CLIENT-006 | Client fetches their event portal data | test_client_portal.py | 200, event + task summary | ⬜ Todo |
| CLIENT-007 | Non-client user cannot access /my-client-event | test_client_portal.py | 403 | ⬜ Todo |

---

## Notes

- All tests use SQLite (via `test.db`) rather than PostgreSQL. The conftest patches `postgresql.UUID` → string and `JSONB` → JSON for SQLite compatibility.
- `DEV_SKIP_AUTH=true` is set in conftest — any Bearer token is accepted. The raw token string becomes the Firebase UID.
- Tests are isolated: `reset_db` fixture drops and recreates all tables before each test, and cleans up the `uploads/` directory.
- Rows marked ⬜ Todo are specified but not yet implemented in test files. ✅ Pass means the test exists and passes.
