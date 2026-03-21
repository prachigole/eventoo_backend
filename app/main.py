import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .exceptions import AppException, app_exception_handler
from .logging_middleware import RequestLoggingMiddleware
from .mdns import advertise, stop
from .routers import events, vendors, candidates, todos, users, invites, tasks, extension_requests, task_photos

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(message)s")


# ── Lifespan: mDNS advertisement ──────────────────────────────────────────────
@asynccontextmanager
async def lifespan(_: FastAPI):
    # Skip mDNS in test / dev-skip-auth mode — tests restart the app many
    # times per run and Zeroconf raises NonUniqueNameException on re-registration.
    if settings.dev_skip_auth:
        yield
        return

    zc = await advertise()   # announce _eventoo._tcp.local. on the LAN
    yield
    await stop(zc)           # clean up on shutdown (Ctrl-C / SIGTERM)


app = FastAPI(
    title="Eventoo API",
    version="1.0.0",
    description="REST API for the Eventoo event management app",
    redirect_slashes=False,
    lifespan=lifespan,
)

# ── Middleware (outermost first) ───────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ─────────────────────────────────────────────────────────
app.add_exception_handler(AppException, app_exception_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = " → ".join(str(x) for x in first.get("loc", [])[1:])
    msg = first.get("msg", "Invalid input")
    detail = f"{field}: {msg}" if field else msg
    return JSONResponse(
        status_code=422,
        content={"success": False, "error": {"code": "VALIDATION_ERROR", "message": detail}},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
        },
    )


# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(events.router,     prefix="/api/v1")
app.include_router(vendors.router,    prefix="/api/v1")
app.include_router(candidates.router, prefix="/api/v1")
app.include_router(todos.router,      prefix="/api/v1")
app.include_router(users.router,      prefix="/api/v1")
app.include_router(invites.router,    prefix="/api/v1")
app.include_router(tasks.router,               prefix="/api/v1")
app.include_router(extension_requests.router,  prefix="/api/v1")
app.include_router(task_photos.router,         prefix="/api/v1")

# ── Static file serving for uploaded photos ────────────────────────────────────
os.makedirs("uploads/task_photos", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
