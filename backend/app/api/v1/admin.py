from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.session import get_db
from app.models import AuditLog, Claim, ClaimStatus, Item, ItemKind, ItemStatus, User
from app.schemas.schemas import AuditOut, StatsOut, UserOut, UserPublic
from app.services.audit import audit

router = APIRouter(tags=["admin"])


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    count = lambda *w: db.scalar(select(func.count()).select_from(Item).where(*w)) or 0  # noqa: E731
    total = count()
    returned = count(Item.status == ItemStatus.returned)
    items = db.scalars(select(Item)).all()
    since = datetime.now(timezone.utc) - timedelta(days=13)
    daily = Counter(
        i.created_at.date().isoformat() for i in items
        if (i.created_at if i.created_at.tzinfo else i.created_at.replace(tzinfo=timezone.utc)) >= since
    )
    days = [(since + timedelta(days=d)).date().isoformat() for d in range(14)]
    return StatsOut(
        total_items=total,
        open_lost=count(Item.kind == ItemKind.lost, Item.status == ItemStatus.open),
        open_found=count(Item.kind == ItemKind.found, Item.status == ItemStatus.open),
        returned=returned,
        pending_claims=db.scalar(select(func.count()).select_from(Claim).where(Claim.status == ClaimStatus.pending)) or 0,
        return_rate=round(returned / total, 3) if total else 0.0,
        by_category=dict(Counter(i.category for i in items)),
        by_location=dict(Counter(i.location for i in items).most_common(8)),
        daily=[{"date": d, "count": daily.get(d, 0)} for d in days],
    )


@router.get("/leaderboard", response_model=list[UserPublic])
def leaderboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.scalars(select(User).where(User.karma > 0).order_by(User.karma.desc()).limit(10)).all()


@router.get("/admin/users", response_model=list[UserOut])
def users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.scalars(select(User).order_by(User.created_at.desc())).all()


@router.post("/admin/users/{user_id}/toggle-active", response_model=UserOut)
def toggle_active(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    target = db.get(User, user_id)
    if not target:
        raise HTTPException(404, "User not found")
    if target.id == admin.id:
        raise HTTPException(400, "You cannot disable yourself")
    target.is_active = not target.is_active
    audit(db, admin.id, "toggle_active", "user", target.id, active=target.is_active)
    db.commit()
    return target


@router.get("/admin/audit", response_model=list[AuditOut])
def audit_log(limit: int = Query(50, le=200), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)).all()
