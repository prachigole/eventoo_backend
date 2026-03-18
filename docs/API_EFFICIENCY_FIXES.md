# API Efficiency Fixes

Recommended code-level fixes for the issues identified in the efficiency report. These are not yet applied to the codebase — they document the changes needed.

---

## Fix 1: Double `_get_candidate` call in `update_candidate`

**File:** `app/routers/candidates.py`
**Severity:** Medium — 1 extra SQL query per PATCH candidate request

**Current code (lines 108–118):**
```python
candidate = _get_candidate(db, event_id, vendor_id)          # query 1

for field, value in body.model_dump(exclude_unset=True, by_alias=False).items():
    setattr(candidate, field, value)

db.commit()
db.refresh(candidate)

# Reload vendor relation after refresh
candidate = _get_candidate(db, event_id, vendor_id)          # query 2 (redundant)
```

**Problem:** `db.refresh(candidate)` reloads the scalar columns on the existing object. Then `_get_candidate` is called again with `selectinload(Candidate.vendor)` to reload the vendor relation. This results in 2 separate `SELECT` queries after the `UPDATE`.

**Fix:** Use `db.refresh(candidate, attribute_names=["vendor"])` to reload the vendor relation on the existing object without a second full query:
```python
candidate = _get_candidate(db, event_id, vendor_id)

for field, value in body.model_dump(exclude_unset=True, by_alias=False).items():
    setattr(candidate, field, value)

db.commit()
db.refresh(candidate)
db.refresh(candidate, attribute_names=["vendor"])            # reload relation only
# Remove the second _get_candidate() call
```

---

## Fix 2: Three separate queries in `add_candidate`

**File:** `app/routers/candidates.py`
**Severity:** Low — the checks are logically necessary but could be combined

**Current code (lines 67–79):**
```python
_get_owned_event(db, event_id, user.id)   # query 1: verify event ownership

vendor = db.query(Vendor).filter(         # query 2: verify vendor ownership
    Vendor.id == body.vendor_id, Vendor.user_id == user.id
).first()

exists = db.query(Candidate).filter(      # query 3: duplicate check
    Candidate.event_id == event_id, Candidate.vendor_id == body.vendor_id
).first()
```

**Fix option:** Combine the vendor ownership check and duplicate check into one query using a join or subquery. However, the combined query is harder to read and the error messages would need to distinguish between "vendor not found" and "already shortlisted". The current 3-query approach is clear and safe for normal usage. **Recommended only if profiling identifies this as a bottleneck.**

---

## Fix 3: Separate ownership check from candidates query in `list_candidates`

**File:** `app/routers/candidates.py`
**Severity:** Low

**Current code (lines 44–53):**
```python
_get_owned_event(db, event_id, user.id)   # query 1: verify ownership

candidates = (
    db.query(Candidate)                   # query 2: fetch candidates
    .options(selectinload(Candidate.vendor))
    .filter(Candidate.event_id == event_id)
    .order_by(Candidate.created_at)
    .all()
)
```

**Fix option:** Join events and candidates in a single query to verify ownership and fetch candidates at once. This saves one round-trip:
```python
# Verify event ownership AND fetch candidates in one go
event = (
    db.query(Event)
    .options(selectinload(Event.candidates).selectinload(Candidate.vendor))
    .filter(Event.id == event_id, Event.user_id == user.id)
    .first()
)
if not event:
    raise NotFound("Event")
candidates = sorted(event.candidates, key=lambda c: c.created_at)
```

---

## Fix 4: Missing composite indexes for common filter patterns

**File:** `app/models/event.py` and `app/models/vendor.py`
**Severity:** Medium — matters at scale (thousands of events/vendors per user)

**Problem:** The most common query pattern is `WHERE user_id = ? AND status = ?`. With separate indexes on `user_id` and `status`, PostgreSQL may choose the `user_id` index and then filter by status in memory. A composite index would be more efficient.

**Fix for events:**
```python
# In Event.__table_args__:
Index("ix_events_user_status", "user_id", "status"),
Index("ix_events_user_date",   "user_id", "date"),
```

**Fix for vendors:**
```python
# In Vendor.__table_args__:
Index("ix_vendors_user_category", "user_id", "category"),
Index("ix_vendors_user_rating",   "user_id", "rating"),
```

**Alembic migration needed:**
```python
op.create_index("ix_events_user_status",   "events",  ["user_id", "status"])
op.create_index("ix_events_user_date",     "events",  ["user_id", "date"])
op.create_index("ix_vendors_user_category","vendors", ["user_id", "category"])
op.create_index("ix_vendors_user_rating",  "vendors", ["user_id", "rating"])
```

---

## Fix 5: Vendor ILIKE search on 4 columns without full-text index

**File:** `app/routers/vendors.py`
**Severity:** Low for small datasets, medium for large

**Current code (lines 44–50):**
```python
q = q.filter(
    Vendor.name.ilike(term)
    | Vendor.location.ilike(term)
    | Vendor.email.ilike(term)
    | Vendor.price_range.ilike(term)
)
```

**Problem:** Four separate `ILIKE` clauses with leading `%` wildcards cannot use B-tree indexes.

**Fix option A (simple):** Add PostgreSQL trigram indexes:
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX ix_vendors_name_trgm     ON vendors USING gin (name gin_trgm_ops);
CREATE INDEX ix_vendors_location_trgm ON vendors USING gin (location gin_trgm_ops);
```

**Fix option B (comprehensive):** Use PostgreSQL `tsvector` full-text search with a generated column. This is a more significant refactor.

---

## Fix 6: `per_page` maximum of 200 for vendors

**File:** `app/routers/vendors.py`
**Severity:** Low

**Current:** `per_page: int = Query(default=100, ge=1, le=200)`

The Flutter app fetches all vendors in a single request. At 200 vendors per request, with 200 rows + selectinload not applied (vendor list doesn't eagerly load relations), this is acceptable. However, the higher cap compared to events (100) is inconsistent. If vendor count grows, consider reducing to 100 or adding server-side filtering.
