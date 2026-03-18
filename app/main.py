from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .exceptions import AppException, app_exception_handler
from .routers import events, vendors, candidates

app = FastAPI(
    title="Eventoo API",
    version="1.0.0",
    description="REST API for the Eventoo event management app",
    redirect_slashes=False,   # don't redirect /events → /events/
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ─────────────────────────────────────────────────────────
app.add_exception_handler(AppException, app_exception_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # Pick the first validation error and surface it as a readable message
    errors = exc.errors()
    first = errors[0] if errors else {}
    field = " → ".join(str(x) for x in first.get("loc", [])[1:])  # skip "body"
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


# ── Health check ───────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
