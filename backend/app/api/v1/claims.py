from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Claim, ClaimStatus, Item, ItemKind, ItemStatus, Role, User
from app.schemas.schemas import ClaimDecision, ClaimIn, ClaimOut, UserPublic
from app.services.audit import audit
from app.services.notifications import notify
from app.services.similarity import text_similarity

router = APIRouter(tags=["claims"])

RETURN_KARMA = 10


def to_out(c: Claim) -> ClaimOut:
    return ClaimOut(
        id=c.id, item_id=c.item_id, item_title=c.item.title, claimant=UserPublic.model_validate(c.claimant),
        answer=c.answer, verification_score=c.verification_score, status=c.status,
        reviewer_note=c.reviewer_note, created_at=c.created_at, resolved_at=c.resolved_at,
    )


@router.post("/items/{item_id}/claims", response_model=ClaimOut, status_code=201)
def create_claim(item_id: int, body: ClaimIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.kind != ItemKind.found:
        raise HTTPException(400, "Only found items can be claimed")
    if item.owner_id == user.id:
        raise HTTPException(400, "You cannot claim your own item")
    if item.status != ItemStatus.open:
        raise HTTPException(409, f"Item is {item.status.value}")
    dup = db.scalar(select(Claim).where(
        Claim.item_id == item_id, Claim.claimant_id == user.id, Claim.status == ClaimStatus.pending))
    if dup:
        raise HTTPException(409, "You already have a pending claim on this item")
    score = round(text_similarity(body.answer, item.secret_detail or ""), 3)
    claim = Claim(item_id=item_id, claimant_id=user.id, answer=body.answer, verification_score=score)
    db.add(claim)
    db.flush()
    strength = "strong" if score >= 0.5 else "weak"
    notify(db, item.owner_id, "claim", f"{user.name} claimed '{item.title}' ({strength} verification)",
           link="/claims/incoming")
    audit(db, user.id, "create", "claim", claim.id, item_id=item_id, score=score)
    db.commit()
    return to_out(claim)


@router.get("/claims/mine", response_model=list[ClaimOut])
def my_claims(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Claim).where(Claim.claimant_id == user.id).order_by(Claim.created_at.desc())).all()
    return [to_out(c) for c in rows]


@router.get("/claims/incoming", response_model=list[ClaimOut])
def incoming_claims(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Claims on found items I posted (admins see all)."""
    stmt = select(Claim).join(Item).order_by(Claim.created_at.desc())
    if user.role != Role.admin:
        stmt = stmt.where(Item.owner_id == user.id)
    return [to_out(c) for c in db.scalars(stmt).all()]


def _load_for_review(db: Session, claim_id: int, user: User) -> Claim:
    claim = db.get(Claim, claim_id)
    if not claim:
        raise HTTPException(404, "Claim not found")
    if claim.item.owner_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Only the finder or an admin can review this claim")
    return claim


@router.post("/claims/{claim_id}/decision", response_model=ClaimOut)
def decide(claim_id: int, body: ClaimDecision, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    claim = _load_for_review(db, claim_id, user)
    if claim.status != ClaimStatus.pending:
        raise HTTPException(409, f"Claim already {claim.status.value}")
    claim.status = ClaimStatus.approved if body.approve else ClaimStatus.rejected
    claim.reviewer_note = body.note
    claim.resolved_at = datetime.now(timezone.utc)
    if body.approve:
        claim.item.status = ItemStatus.claimed
        # competing pending claims are closed automatically
        for other in claim.item.claims:
            if other.id != claim.id and other.status == ClaimStatus.pending:
                other.status = ClaimStatus.rejected
                other.reviewer_note = "Another claim was approved"
                other.resolved_at = claim.resolved_at
                notify(db, other.claimant_id, "claim", f"Your claim on '{claim.item.title}' was not approved")
    verb = "approved" if body.approve else "rejected"
    notify(db, claim.claimant_id, "claim", f"Your claim on '{claim.item.title}' was {verb}", link="/claims/mine")
    audit(db, user.id, verb, "claim", claim.id)
    db.commit()
    return to_out(claim)


@router.post("/claims/{claim_id}/returned", response_model=ClaimOut)
def confirm_return(claim_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Finder confirms the handoff happened: item becomes `returned` and the finder earns karma."""
    claim = _load_for_review(db, claim_id, user)
    if claim.status != ClaimStatus.approved or claim.item.status != ItemStatus.claimed:
        raise HTTPException(409, "Claim must be approved before confirming a return")
    claim.item.status = ItemStatus.returned
    claim.item.owner.karma += RETURN_KARMA
    notify(db, claim.claimant_id, "return", f"'{claim.item.title}' marked as returned. Glad it found you!")
    audit(db, user.id, "returned", "claim", claim.id)
    db.commit()
    return to_out(claim)
