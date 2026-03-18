# Eventoo API Reference

Base URL: `http://localhost:8000`
All protected endpoints require: `Authorization: Bearer <firebase-id-token>`

All responses are wrapped in a standard envelope:

**Success:**
```json
{"success": true, "data": {...}, "message": "optional string"}
```

**Paginated:**
```json
{
  "success": true,
  "data": {
    "items": [...],
    "meta": {"total": 10, "page": 1, "perPage": 50, "totalPages": 1}
  }
}
```

**Error:**
```json
{"success": false, "error": {"code": "NOT_FOUND", "message": "Event not found"}}
```

---

## Health

### GET /health

Returns server status. No auth required.

**Response 200:**
```json
{"status": "ok"}
```

```bash
curl http://localhost:8000/health
```

---

## Events

All event endpoints require authentication.

### GET /api/v1/events

List events owned by the authenticated user.

**Query parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| status | string | — | Filter by status: `upcoming`, `ongoing`, `past`, `cancelled` |
| category | string | — | Filter by category: `music`, `corporate`, `wedding`, `sports`, `art`, `food` |
| search | string | — | Case-insensitive title search (max 100 chars) |
| page | int | 1 | Page number (≥1) |
| per_page | int | 50 | Items per page (1–100) |

**Response 200:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "title": "Summer Concert",
        "date": "2026-06-15",
        "time": "7:00 PM",
        "venue": "Phoenix Mall",
        "city": "Mumbai",
        "category": "music",
        "status": "upcoming",
        "attendeeCount": 0,
        "capacity": 500,
        "coverGradient": null,
        "createdAt": "2026-03-18T10:00:00Z",
        "updatedAt": "2026-03-18T10:00:00Z"
      }
    ],
    "meta": {"total": 1, "page": 1, "perPage": 50, "totalPages": 1}
  }
}
```

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/events?status=upcoming&page=1"
```

---

### POST /api/v1/events

Create a new event.

**Request body (camelCase, all required fields unless noted):**

| Field | Type | Required | Notes |
|---|---|---|---|
| title | string | Yes | 1–255 chars |
| date | string | Yes | YYYY-MM-DD |
| venue | string | No | Default `""` |
| category | string | Yes | `music`\|`corporate`\|`wedding`\|`sports`\|`art`\|`food` |
| status | string | No | Default `upcoming` |
| attendeeCount | int | No | Default 0, ≥0 |
| capacity | int | No | Default 100, ≥1 |
| time | string | No | |
| city | string | No | |
| description | string | No | |
| coverGradient | int[] | No | ARGB color values |
| clientName | string | No | |
| clientPhone | string | No | |
| clientEmail | string | No | |
| budget | int | No | ₹ thousands, ≥0 |
| notes | string | No | |

**Response 201:**
```json
{
  "success": true,
  "data": {"id": "uuid", "title": "Summer Concert", ...},
  "message": "Event created"
}
```

**Response 422:** Validation error (missing required field, invalid enum value, etc.)

```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Summer Concert","date":"2026-06-15","category":"music","capacity":500}'
```

---

### GET /api/v1/events/{event_id}

Get full event detail including candidates with vendor data.

**Path param:** `event_id` — UUID

**Response 200:** Full EventDetail schema including `candidates` array (each with nested `vendor` object).

**Response 404:** Event not found (or not owned by caller).

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/events/123e4567-e89b-12d3-a456-426614174000
```

---

### PATCH /api/v1/events/{event_id}

Update event fields. Only provided fields are updated (true PATCH semantics).

**Request body:** Same fields as POST, all optional. `title` must be 1–255 chars if provided.

**Response 200:**
```json
{"success": true, "data": {...}, "message": "Event updated"}
```

**Response 404:** Event not found or not owned by caller.

```bash
curl -X PATCH http://localhost:8000/api/v1/events/UUID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"ongoing","attendeeCount":250}'
```

---

### DELETE /api/v1/events/{event_id}

Delete an event and all its candidates (cascade).

**Response 200:**
```json
{"success": true, "data": null, "message": "Event deleted"}
```

**Response 404:** Event not found or not owned by caller.

```bash
curl -X DELETE http://localhost:8000/api/v1/events/UUID \
  -H "Authorization: Bearer $TOKEN"
```

---

## Vendors

### GET /api/v1/vendors

List vendors owned by the authenticated user.

**Query parameters:**

| Name | Type | Default | Description |
|---|---|---|---|
| category | string | — | Filter by vendor category |
| search | string | — | Searches name, location, email, price_range (max 100 chars) |
| min_rating | float | — | Minimum rating (0.0–5.0) |
| page | int | 1 | Page number |
| per_page | int | 100 | Items per page (1–200) |

Results ordered by rating descending, then name ascending.

**Response 200:** Paginated list of VendorSummary objects.

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/vendors?category=catering&min_rating=4.0"
```

---

### POST /api/v1/vendors

Create a new vendor.

**Request body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| name | string | Yes | 1–255 chars |
| category | string | Yes | `catering`\|`photography`\|`music`\|`decoration`\|`venue`\|`lighting`\|`av`\|`security`\|`transport`\|`other` |
| phone | string | Yes | 1–50 chars |
| email | string | No | |
| location | string | No | |
| priceRange | string | No | |
| rating | float | No | Default 0.0, range 0.0–5.0 |
| eventsWorked | int | No | Default 0, ≥0 |
| notes | string | No | |

**Response 201:** Full VendorDetail object.

```bash
curl -X POST http://localhost:8000/api/v1/vendors \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Bloom Decor","category":"decoration","phone":"+919876543210","rating":4.5}'
```

---

### GET /api/v1/vendors/{vendor_id}

Get full vendor detail.

**Response 200:** VendorDetail (includes `notes`, `createdAt`, `updatedAt`).
**Response 404:** Vendor not found or not owned by caller.

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/vendors/UUID
```

---

### PATCH /api/v1/vendors/{vendor_id}

Update vendor fields. All fields optional.

**Response 200:**
```json
{"success": true, "data": {...}, "message": "Vendor updated"}
```

```bash
curl -X PATCH http://localhost:8000/api/v1/vendors/UUID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating":4.8,"eventsWorked":12}'
```

---

### DELETE /api/v1/vendors/{vendor_id}

Delete a vendor.

**Response 200:**
```json
{"success": true, "data": null, "message": "Vendor deleted"}
```

```bash
curl -X DELETE http://localhost:8000/api/v1/vendors/UUID \
  -H "Authorization: Bearer $TOKEN"
```

---

## Candidates (Shortlisting)

Candidates link a vendor to an event's shortlist. The `{vendor_id}` path param in PATCH/DELETE is the **vendor's UUID**, not a candidate UUID.

### GET /api/v1/events/{event_id}/candidates

List all shortlisted vendors for an event.

**Response 200:**
```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "eventId": "uuid",
      "vendorId": "uuid",
      "status": "shortlisted",
      "quotedCost": null,
      "notes": null,
      "rejectionReason": null,
      "vendor": {
        "id": "uuid", "name": "Bloom Decor", "category": "decoration",
        "phone": "+919876543210", "email": null, "location": null,
        "priceRange": null, "rating": 4.5, "eventsWorked": 3
      },
      "createdAt": "2026-03-18T10:00:00Z",
      "updatedAt": "2026-03-18T10:00:00Z"
    }
  ]
}
```

**Response 404:** Event not found or not owned by caller.

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/events/EVENT_UUID/candidates
```

---

### POST /api/v1/events/{event_id}/candidates

Add a vendor to the event's shortlist.

**Request body:**

| Field | Type | Required | Notes |
|---|---|---|---|
| vendorId | string (UUID) | Yes | Must be owned by the caller |
| quotedCost | int | No | ₹ thousands, ≥0 |
| notes | string | No | |

**Response 201:** CandidateWithVendor object with nested vendor data.

**Response 404:** Event or vendor not found (or not owned by caller).
**Response 409:** Vendor already shortlisted for this event.

```bash
curl -X POST http://localhost:8000/api/v1/events/EVENT_UUID/candidates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vendorId":"VENDOR_UUID","quotedCost":50}'
```

---

### PATCH /api/v1/events/{event_id}/candidates/{vendor_id}

Update a candidate's status, quoted cost, notes, or rejection reason.

**Request body (all optional):**

| Field | Type | Notes |
|---|---|---|
| status | string | `shortlisted`\|`awaitingConfirmation`\|`finalised`\|`rejected` |
| quotedCost | int | ₹ thousands, ≥0 |
| notes | string | |
| rejectionReason | string | |

**Response 200:** Updated CandidateWithVendor.
**Response 404:** Event or candidate not found.

```bash
curl -X PATCH "http://localhost:8000/api/v1/events/EVENT_UUID/candidates/VENDOR_UUID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"finalised","quotedCost":75}'
```

---

### DELETE /api/v1/events/{event_id}/candidates/{vendor_id}

Remove a vendor from the event's shortlist.

**Response 200:**
```json
{"success": true, "data": null, "message": "Vendor removed from shortlist"}
```

**Response 404:** Event or candidate not found.

```bash
curl -X DELETE "http://localhost:8000/api/v1/events/EVENT_UUID/candidates/VENDOR_UUID" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Status Code Summary

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 401 | Missing or invalid Authorization header |
| 404 | Resource not found (or not owned by caller) |
| 409 | Conflict (duplicate shortlisting) |
| 422 | Validation error |
| 500 | Internal server error |
