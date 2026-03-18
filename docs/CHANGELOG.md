# Changelog

## [Unreleased]

## [1.0.0] — 2026-03-18

### Added
- Initial FastAPI backend with events, vendors, candidates CRUD
- Firebase JWT authentication with DEV_SKIP_AUTH mode
- PostgreSQL database with SQLAlchemy ORM and Alembic migrations
- CORS middleware configured for local development
- Comprehensive error handling with AppException and validation error handlers
- In-process user lookup cache to avoid redundant DB queries per request
- Database connection pooling (pool_size=10, max_overflow=20, pool_pre_ping=True)
- Eager loading for candidate→vendor relationships (selectinload)
- camelCase JSON aliases on all schemas via pydantic alias_generator
- Full Alembic migration (0001_initial.py) covering all tables and enum types
