"""
Request/response logging middleware.

Each request prints two lines:
  → METHOD /path  [req_id]  user=<uid|anon>
  ← 200 OK  42ms  [req_id]

Color legend:
  cyan    → incoming request
  green   ← 2xx success
  yellow  ← 3xx / 4xx client error
  red     ← 5xx server error
  dim     timing + metadata
"""

import time
import uuid
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

# ── ANSI colours ──────────────────────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
BLUE   = "\033[34m"
MAGENTA= "\033[35m"

# ── Method colours ─────────────────────────────────────────────────────────────
_METHOD_COLOR = {
    "GET":    BLUE,
    "POST":   GREEN,
    "PATCH":  YELLOW,
    "PUT":    YELLOW,
    "DELETE": RED,
}

# ── Standard Python logger (goes to stdout via uvicorn) ───────────────────────
logger = logging.getLogger("eventoo.api")


def _method_tag(method: str) -> str:
    color = _METHOD_COLOR.get(method, MAGENTA)
    return f"{BOLD}{color}{method:<7}{RESET}"


def _status_tag(status: int) -> str:
    if status < 300:
        color = GREEN
    elif status < 500:
        color = YELLOW
    else:
        color = RED
    return f"{BOLD}{color}{status}{RESET}"


def _uid_from_request(request: Request) -> str:
    """Best-effort extraction of the caller's UID from the Authorization header."""
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return "anon"
    token = auth.split(" ", 1)[1]
    # In DEV_SKIP_AUTH mode the raw token string is the uid.
    # In production the uid lives inside the Firebase JWT payload — we don't
    # decode here (no secret available at middleware level) so we show a prefix.
    if len(token) < 40:          # looks like a dev uid, show it in full
        return token
    return token[:8] + "…"       # truncate real JWTs


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        req_id  = uuid.uuid4().hex[:8]          # short correlation id
        method  = request.method
        path    = request.url.path
        qs      = f"?{request.url.query}" if request.url.query else ""
        uid     = _uid_from_request(request)
        start   = time.perf_counter()

        # ── Incoming line ─────────────────────────────────────────────────────
        logger.info(
            f"{CYAN}→{RESET} {_method_tag(method)} "
            f"{BOLD}{path}{qs}{RESET}  "
            f"{DIM}[{req_id}]  user={uid}{RESET}"
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error(
                f"{RED}✗{RESET} {_method_tag(method)} "
                f"{BOLD}{path}{RESET}  "
                f"{RED}UNHANDLED {type(exc).__name__}{RESET}  "
                f"{DIM}{elapsed_ms:.1f}ms  [{req_id}]{RESET}"
            )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        status     = response.status_code

        # ── Outgoing line ─────────────────────────────────────────────────────
        logger.info(
            f"{CYAN}←{RESET} {_status_tag(status)}  "
            f"{DIM}{elapsed_ms:.1f}ms  [{req_id}]{RESET}"
        )

        # Attach the correlation id to every response so clients can trace it
        response.headers["X-Request-Id"] = req_id
        return response
