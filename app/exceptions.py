from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message


class NotFound(AppException):
    def __init__(self, resource: str):
        super().__init__(404, "NOT_FOUND", f"{resource} not found")


class Forbidden(AppException):
    def __init__(self):
        super().__init__(403, "FORBIDDEN", "You do not have access to this resource")


class Conflict(AppException):
    def __init__(self, message: str):
        super().__init__(409, "CONFLICT", message)


class BadRequest(AppException):
    def __init__(self, message: str):
        super().__init__(400, "BAD_REQUEST", message)


# ── FastAPI exception handler ──────────────────────────────────────────────────
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": exc.code, "message": exc.message}},
    )
