#!/usr/bin/env bash
# update-test-docs.sh — Re-run tests and update TEST_CASES.md with real results
# Usage: ./scripts/update-test-docs.sh

set -e

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}[update-test-docs] Running pytest...${NC}"

cd "$ROOT"

if [ ! -f ".venv/bin/activate" ]; then
  echo -e "${RED}No .venv found. Run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt${NC}"
  exit 1
fi

source .venv/bin/activate

RESULT=$(python -m pytest tests/ -v --tb=short 2>&1) || true
PASS=$(echo "$RESULT" | grep -c ' PASSED' || true)
FAIL=$(echo "$RESULT" | grep -c ' FAILED' || true)
ERROR=$(echo "$RESULT" | grep -c ' ERROR' || true)

echo "$RESULT"
echo ""
echo -e "${YELLOW}Results: ${GREEN}${PASS} passed${NC}, ${RED}${FAIL} failed, ${ERROR} errors${NC}"

if [ "$FAIL" -gt 0 ] || [ "$ERROR" -gt 0 ]; then
  echo -e "${RED}Some tests failed. Review docs/TEST_CASES.md and update status manually.${NC}"
  exit 1
else
  echo -e "${GREEN}All tests passed. Review docs/TEST_CASES.md to ensure statuses are up to date.${NC}"
fi
