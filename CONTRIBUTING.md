# Contributing to Eventoo Backend

## Commit Message Convention

Use the Conventional Commits format:

```
<type>(<scope>): <short summary>

[optional body]

[optional footer]
```

**Types:**
- `feat` — new feature or endpoint
- `fix` — bug fix
- `refactor` — code change that neither fixes a bug nor adds a feature
- `docs` — documentation only
- `test` — adding or updating tests
- `chore` — build, config, CI changes

**Examples:**
```
feat(events): add category filter to list endpoint
fix(candidates): avoid double _get_candidate query in update
docs(api): update API_REFERENCE with new query params
test(vendors): add min_rating filter test
```

## Workflow

1. Create a feature branch: `git checkout -b feat/my-feature`
2. Make changes — do **not** modify test fixtures or shared config without discussion
3. Run tests: `source .venv/bin/activate && python -m pytest tests/ -v --tb=short`
   - Output shows every failing test by name. A clean run prints only green dots and a summary line.
4. Run the pre-commit hook manually if needed: `./scripts/pre-commit-validate.sh`
5. Commit with a conventional message
6. Open a pull request against `main`

## Pre-commit Hook

Install the pre-commit hook to catch issues before committing:

```bash
cp scripts/pre-commit-validate.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

The hook checks:
- `.env` is not staged
- Firebase credentials are not staged
- Python syntax is valid for all staged `.py` files
- All tests pass (if app or test files are staged)

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- All new endpoints must have a corresponding test in `tests/`
- All Pydantic schemas must inherit `CamelSchema` for consistent JSON output
- New DB columns require an Alembic migration in `alembic/versions/`

## Code Quality — Keep the Codebase Lean

- **Routinely delete unused code.** Before merging, remove any functions, imports, models, schemas, or router files that are no longer referenced anywhere. Dead code increases bundle size, slows onboarding, and creates maintenance risk.
- Use `grep` or your IDE's "Find Usages" to confirm a symbol is truly unused before deleting it.
- Unused Alembic migrations should never be left dangling — either apply them or delete them.

## Environment Variables

Never commit `.env`. Use `.env.example` to document new variables:
```
# .env.example
DATABASE_URL=postgresql://user:password@localhost:5432/eventoo
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
DEV_SKIP_AUTH=false
```

## Testing Guidelines

- Use SQLite (`test.db`) for all tests — no PostgreSQL required locally
- `DEV_SKIP_AUTH=true` is set in conftest — do not override it in individual tests
- Each test must clean up after itself — `reset_db` fixture handles this automatically
- Test IDs must match the format in `docs/TEST_CASES.md`
- **Every API endpoint must have test coverage for all three response types:**
  - **Empty / not-found** — e.g. list returns `[]`, GET on unknown ID returns 404
  - **Success** — valid input returns the expected status code and response shape
  - **Error** — invalid input (missing field, wrong type, bad enum value) returns 4xx
- Run the full suite before opening a PR. The test command must complete without failures:
  ```bash
  python -m pytest tests/ -v --tb=short
  ```
  Any test that does not pass must be fixed or explicitly documented with a skip reason before merging.
