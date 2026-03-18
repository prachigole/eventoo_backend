# API Efficiency Report

Analysis of every endpoint against common performance issues. Based on static code review of the actual router, model, and schema files.

---

## Summary Table

| Endpoint | N+1 Risk | Missing Index | Unbounded Query | Notes |
|---|---|---|---|---|
| GET /health | — | — | — | No DB access |
| GET /events | None | None | Per-page capped at 100 | total=len(events) avoids COUNT |
| POST /events | None | None | — | Single INSERT + refresh |
| GET /events/{id} | **None** — selectinload | None | — | Eager loads candidates→vendor in 2 queries |
| PATCH /events/{id} | None | None | — | _get_owned: 1 query, then UPDATE |
| DELETE /events/{id} | None | None | — | _get_owned: 1 query, then DELETE |
| GET /vendors | None | None | Per-page capped at 200 | total=len(vendors) |
| POST /vendors | None | None | — | Single INSERT + refresh |
| GET /vendors/{id} | None | None | — | _get_owned: 1 query |
| PATCH /vendors/{id} | None | None | — | _get_owned + UPDATE |
| DELETE /vendors/{id} | None | None | — | _get_owned + DELETE |
| GET /events/{id}/candidates | **None** — selectinload | None | Unbounded | All candidates returned, no pagination |
| POST /events/{id}/candidates | None | None | — | 3 queries: owned_event + vendor + duplicate check |
| PATCH /events/{id}/candidates/{vid} | None | None | — | `_get_candidate` called twice (see Fixes) |
| DELETE /events/{id}/candidates/{vid} | None | None | — | _get_owned_event + raw Candidate query |

---

## Detailed Analysis

### 1. N+1 Queries

**Status: Not present in production paths.**

- `GET /events/{id}` uses `selectinload(Event.candidates).selectinload(Candidate.vendor)` — loads all candidates and their vendors in exactly 2 additional SQL queries regardless of candidate count.
- `GET /events/{id}/candidates` uses `selectinload(Candidate.vendor)` — 1 additional query for all vendors.
- `_get_candidate()` helper uses `selectinload(Candidate.vendor)` — safe for single-row fetches.
- `GET /events` (list) returns `EventSummary` schema which **does not include candidates** — no risk.
- `GET /vendors` returns `VendorSummary` — no nested relations loaded.

### 2. Missing Indexes

**Status: All critical indexes are present.**

- `users`: `ix_users_firebase_uid` — used on every auth request.
- `events`: `ix_events_user_id`, `ix_events_status`, `ix_events_date` — covers all filter and sort paths.
- `vendors`: `ix_vendors_user_id`, `ix_vendors_category`, `ix_vendors_rating` — covers all filter and ORDER BY paths.
- `candidates`: `ix_candidates_event_id`, `ix_candidates_vendor_id`, `ix_candidates_status`, and `uq_candidate_event_vendor` unique constraint.

**One missing index:** There is no composite index on `(user_id, status)` for events or `(user_id, category)` for vendors. With large datasets, a combined filter query would benefit from these. See `API_EFFICIENCY_FIXES.md`.

### 3. Unbounded Queries

**Candidates endpoint:** `GET /events/{id}/candidates` returns all candidates for an event with no pagination. For events with very large shortlists (hundreds of vendors) this could return a lot of data in one response. In practice, shortlists are small so this is acceptable.

**Vendor search:** `per_page` max is 200 (vs 100 for events). With full-text ILIKE search across 4 columns (`name`, `location`, `email`, `price_range`), this is a multi-column ILIKE scan. For large vendor tables, a PostgreSQL full-text search index would be more efficient.

### 4. In-Process User Cache

`get_or_create_user()` in `database.py` maintains `_uid_to_user_id: dict[str, uuid.UUID]`. After the first request for a given Firebase UID, all subsequent requests in the same process skip the `SELECT * FROM users WHERE firebase_uid = ?` query and use `db.get(User, user_id)` (primary key lookup, which may hit SQLAlchemy's identity map or issue a fast PK query).

**Trade-off:** The cache lives in-process memory. With multiple worker processes (e.g. `--workers 4` in production), each process has its own cache. The first request per process per user still hits the DB. This is intentional and safe because the firebase_uid → user_id mapping is immutable once created.

### 5. COUNT Removal

List endpoints (`GET /events`, `GET /vendors`) return `total=len(events)` (the count of rows already fetched for the current page) rather than issuing a separate `SELECT COUNT(*)`. This is correct for small datasets and avoids an extra round-trip. However, `meta.total` reflects the page count, not the true total across all pages. This is a known design decision — the Flutter client does not currently display total pages.

### 6. Sync vs Async

All route functions use `def` (synchronous) with the synchronous SQLAlchemy `Session`. FastAPI runs sync route handlers in a thread pool automatically. This is the correct approach for synchronous SQLAlchemy — using `async def` with a sync session would block the event loop. The alternative would be to adopt `asyncpg` + SQLAlchemy async sessions, which is a larger refactor.

### 7. Connection Pooling

`database.py` creates the engine with:
```python
pool_size=10,
max_overflow=20,
pool_pre_ping=True,
```

- `pool_size=10`: 10 persistent connections
- `max_overflow=20`: up to 20 additional connections under load (total 30)
- `pool_pre_ping=True`: issues a cheap `SELECT 1` before reusing a connection to detect stale connections dropped by the DB or network

This is appropriate for a single-process development server. For multi-worker production, each worker process maintains its own pool, so total connections = workers × pool_size.
