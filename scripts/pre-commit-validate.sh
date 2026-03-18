#!/usr/bin/env bash
# pre-commit-validate.sh — Eventoo Backend
# Runs fast checks before every commit. Install as a git hook:
#   cp scripts/pre-commit-validate.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit

set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}[pre-commit] Running backend validation...${NC}"

# ── 1. Check for .env file accidentally staged ────────────────────────────────
if git diff --cached --name-only | grep -qE '^\.env$'; then
  echo -e "${RED}[pre-commit] ERROR: .env file is staged. Remove it:${NC}"
  echo "  git reset HEAD .env"
  exit 1
fi

# ── 2. Check for firebase credentials accidentally staged ─────────────────────
if git diff --cached --name-only | grep -qE 'firebase.*credentials.*\.json$|service.account.*\.json$'; then
  echo -e "${RED}[pre-commit] ERROR: Firebase credentials file is staged. Remove it.${NC}"
  exit 1
fi

# ── 3. Python syntax check on staged .py files ───────────────────────────────
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)
if [ -n "$STAGED_PY" ]; then
  echo -e "${YELLOW}[pre-commit] Checking Python syntax...${NC}"
  for f in $STAGED_PY; do
    python3 -m py_compile "$f" 2>&1 || {
      echo -e "${RED}[pre-commit] Syntax error in $f${NC}"
      exit 1
    }
  done
  echo -e "${GREEN}[pre-commit] Python syntax OK${NC}"
fi

# ── 4. Run pytest if test files are staged or app files changed ───────────────
CHANGED_APP=$(git diff --cached --name-only | grep '^app/' || true)
CHANGED_TESTS=$(git diff --cached --name-only | grep '^tests/' || true)

if [ -n "$CHANGED_APP" ] || [ -n "$CHANGED_TESTS" ]; then
  if [ -f ".venv/bin/activate" ]; then
    echo -e "${YELLOW}[pre-commit] Running tests...${NC}"
    source .venv/bin/activate
    python -m pytest tests/ -q --tb=short 2>&1 || {
      echo -e "${RED}[pre-commit] Tests failed. Fix them before committing.${NC}"
      exit 1
    }
    echo -e "${GREEN}[pre-commit] All tests passed${NC}"
  else
    echo -e "${YELLOW}[pre-commit] No .venv found, skipping tests${NC}"
  fi
fi

echo -e "${GREEN}[pre-commit] All checks passed${NC}"
