# Test Cases — Eventoo Backend

Master test plan for the pytest test suite. Run with:
```bash
source .venv/bin/activate
python -m pytest tests/ -v --tb=short
```

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

## Notes

- All tests use SQLite (in-memory via `test.db`) rather than PostgreSQL. SQLite does not support PostgreSQL-specific types (`UUID`, `JSONB`, `Enum`), so the test setup uses SQLAlchemy's `create_all` which translates types to SQLite equivalents. `UUID` is stored as TEXT, `JSONB` as TEXT, Enum as VARCHAR.
- `DEV_SKIP_AUTH=true` is set in the `client` fixture so all tests pass any string as a Bearer token. The uid derived from the raw token string is used as the Firebase UID.
- Tests are isolated: `reset_db` fixture drops and recreates all tables before each test.
