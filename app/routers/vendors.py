import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..exceptions import NotFound
from ..models.vendor import Vendor, VendorCategory
from ..schemas.common import ok, paginated
from ..schemas.vendor import VendorCreate, VendorDetail, VendorSummary, VendorUpdate

router = APIRouter(prefix="/vendors", tags=["Vendors"])


def _get_owned(db: Session, vendor_id: uuid.UUID, user_id: uuid.UUID) -> Vendor:
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id, Vendor.user_id == user_id).first()
    if not vendor:
        raise NotFound("Vendor")
    return vendor


# ── GET /vendors ──────────────────────────────────────────────────────────────
@router.get("")
def list_vendors(
    category: VendorCategory | None = None,
    search: str | None = Query(default=None, max_length=100),
    min_rating: float | None = Query(default=None, ge=0.0, le=5.0),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    q = db.query(Vendor).filter(Vendor.user_id == user.id)

    if category:
        q = q.filter(Vendor.category == category)
    if min_rating is not None:
        q = q.filter(Vendor.rating >= min_rating)
    if search:
        term = f"%{search}%"
        q = q.filter(
            Vendor.name.ilike(term)
            | Vendor.location.ilike(term)
            | Vendor.email.ilike(term)
            | Vendor.price_range.ilike(term)
        )

    vendors = q.order_by(Vendor.rating.desc(), Vendor.name).offset((page - 1) * per_page).limit(per_page).all()

    return paginated(
        items=[VendorSummary.model_validate(v).model_dump(by_alias=True) for v in vendors],
        total=len(vendors),
        page=page,
        per_page=per_page,
    )


# ── POST /vendors ─────────────────────────────────────────────────────────────
@router.post("", status_code=201)
def create_vendor(
    body: VendorCreate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)

    vendor = Vendor(**body.model_dump(by_alias=False), user_id=user.id)
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    return ok(VendorDetail.model_validate(vendor).model_dump(by_alias=True), "Vendor created")


# ── GET /vendors/{id} ─────────────────────────────────────────────────────────
@router.get("/{vendor_id}")
def get_vendor(
    vendor_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    vendor = _get_owned(db, vendor_id, user.id)

    return ok(VendorDetail.model_validate(vendor).model_dump(by_alias=True))


# ── PATCH /vendors/{id} ───────────────────────────────────────────────────────
@router.patch("/{vendor_id}")
def update_vendor(
    vendor_id: uuid.UUID,
    body: VendorUpdate,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    vendor = _get_owned(db, vendor_id, user.id)

    for field, value in body.model_dump(exclude_unset=True, by_alias=False).items():
        setattr(vendor, field, value)

    db.commit()
    db.refresh(vendor)

    return ok(VendorDetail.model_validate(vendor).model_dump(by_alias=True), "Vendor updated")


# ── DELETE /vendors/{id} ──────────────────────────────────────────────────────
@router.delete("/{vendor_id}", status_code=200)
def delete_vendor(
    vendor_id: uuid.UUID,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    user = get_or_create_user(db, token.uid, token.phone)
    vendor = _get_owned(db, vendor_id, user.id)

    db.delete(vendor)
    db.commit()

    return ok(None, "Vendor deleted")
