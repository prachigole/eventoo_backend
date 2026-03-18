# Eventoo Backend

REST API for the Eventoo event management mobile app. Handles events, vendors, and candidate shortlisting with Firebase JWT authentication.

## Tech Stack

| Component | Version |
|---|---|
| Python | 3.11+ |
| FastAPI | 0.115.5 |
| Uvicorn | 0.32.1 |
| SQLAlchemy | 2.0.36 |
| Alembic | 1.14.0 |
| psycopg2-binary | 2.9.10 |
| Pydantic | 2.10.3 |
| pydantic-settings | 2.7.0 |
| firebase-admin | 6.5.0 |
| python-dotenv | 1.0.1 |

## Local Setup

### 1. Clone and create virtual environment

```bash
git clone https://github.com/prachigole/eventoo_backend.git
cd eventoo_backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/eventoo
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
DEV_SKIP_AUTH=false
```

For local development without a real Firebase project, set `DEV_SKIP_AUTH=true`. In this mode the backend decodes the JWT payload without verifying the signature, so any token works.

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Start the server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Swagger UI is available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Documentation

- [API Reference](API_REFERENCE.md) — all 15 endpoints with curl examples
- [Database Schema](DATABASE_SCHEMA.md) — tables, indexes, ER diagram
- [Architecture](ARCHITECTURE.md) — request lifecycle, env vars, error formats
- [API Efficiency Report](API_EFFICIENCY_REPORT.md) — performance audit
- [API Efficiency Fixes](API_EFFICIENCY_FIXES.md) — recommended code-level fixes
- [Test Cases](TEST_CASES.md) — master test plan
- [Changelog](CHANGELOG.md)
- [Contributing](../CONTRIBUTING.md)
