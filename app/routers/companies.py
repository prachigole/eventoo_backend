import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import TokenData, verify_token
from ..database import get_db, get_or_create_user
from ..exceptions import Forbidden
from ..models.company import Company
from ..models.user import User
from ..schemas.common import ok
from ..schemas.company import CompanyEmployeeOut, CompanyOut

router = APIRouter(tags=["Companies"])


# ── GET /companies/search?q= ───────────────────────────────────────────────────
@router.get("/companies/search")
def search_companies(
    q: str = "",
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """Live autocomplete for company names. Used on the onboarding screen."""
    get_or_create_user(db, token.uid, token.phone)   # ensures user exists
    if not q.strip():
        return ok([])
    companies = (
        db.query(Company)
        .filter(func.lower(Company.name).contains(q.strip().lower()))
        .order_by(Company.name)
        .limit(10)
        .all()
    )
    return ok([CompanyOut.model_validate(c).model_dump(by_alias=True) for c in companies])


# ── POST /companies/join-or-create ─────────────────────────────────────────────
class _JoinOrCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., pattern="^(manager|employee)$")
    user_name: str = Field(..., min_length=1, max_length=200, alias="userName")

    model_config = {"populate_by_name": True}


@router.post("/companies/join-or-create", status_code=200)
def join_or_create_company(
    body: _JoinOrCreateBody,
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """
    Onboarding endpoint — called once after first login.
    Finds or creates a company by case-insensitive name, sets the user's
    role, display name, and company_id.
    """
    from ..schemas.user import UserOut

    user = get_or_create_user(db, token.uid, token.phone)

    # Case-insensitive lookup
    company = (
        db.query(Company)
        .filter(func.lower(Company.name) == body.name.strip().lower())
        .first()
    )
    if not company:
        company = Company(name=body.name.strip())
        db.add(company)
        db.flush()   # get company.id before commit

    user.name = body.user_name.strip()
    user.role = body.role
    user.company_id = company.id
    db.commit()
    db.refresh(user)

    return ok(UserOut.model_validate(user), "Onboarding complete")


# ── GET /my-company/employees ──────────────────────────────────────────────────
@router.get("/my-company/employees")
def list_company_employees(
    db: Session = Depends(get_db),
    token: TokenData = Depends(verify_token),
):
    """
    Returns all employees in the calling user's company.
    Used by managers for task assignment and the My Team screen.
    """
    user = get_or_create_user(db, token.uid, token.phone)
    if not user.company_id:
        raise Forbidden()

    employees = (
        db.query(User)
        .filter(
            User.company_id == user.company_id,
            User.role == "employee",
        )
        .order_by(User.name)
        .all()
    )

    result = []
    for emp in employees:
        display_name = emp.name or emp.phone or str(emp.id)[:8]
        result.append(
            CompanyEmployeeOut(
                id=emp.id,
                name=display_name,
                phone=emp.phone,
            ).model_dump(by_alias=True)
        )

    return ok(result)
