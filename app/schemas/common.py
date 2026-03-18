import math
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

T = TypeVar("T")


# ── Base schema ────────────────────────────────────────────────────────────────
# All schemas inherit this.  Enables:
#   - ORM mode (from_attributes)
#   - camelCase aliases in JSON (price_range → priceRange)
#   - Accept both snake_case and camelCase on input
class CamelSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
    )


# ── Response envelopes ─────────────────────────────────────────────────────────
class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: str | None = None


class PaginationMeta(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int


class PaginatedData(BaseModel, Generic[T]):
    items: list[T]
    meta: PaginationMeta


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail


# ── Helper builders ────────────────────────────────────────────────────────────
def ok(data: Any, message: str | None = None) -> dict:
    return {"success": True, "data": data, "message": message}


def paginated(
    items: list[Any],
    total: int,
    page: int,
    per_page: int,
) -> dict:
    return {
        "success": True,
        "data": {
            "items": items,
            "meta": {
                "total": total,
                "page": page,
                "perPage": per_page,
                "totalPages": math.ceil(total / per_page) if per_page > 0 else 0,
            },
        },
    }
