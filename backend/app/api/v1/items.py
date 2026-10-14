from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import Item, ItemKind, ItemStatus, Role, User
from app.schemas.schemas import ItemOut, ItemUpdate, MatchOut, Page, UserPublic
from app.services.audit import audit
from app.services.matching import find_matches_for
from app.services.notifications import notify
from app.services.storage import save_image

router = APIRouter(prefix="/items", tags=["items"])

CATEGORIES = ["electronics", "documents", "wallet", "keys", "clothing", "bags", "books", "accessories", "other"]


def to_out(item: Item, viewer: User | None, claim_count: int = 0) -> ItemOut:
    can_see_secret = viewer is not None and (viewer.id == item.owner_id or viewer.role == Role.admin)
    return ItemOut(
        id=item.id, kind=item.kind, status=item.status, title=item.title, description=item.description,
        category=item.category, location=item.location, event_time=item.event_time,
        image_url=f"/uploads/{item.image_path}" if item.image_path else None,
        owner=UserPublic.model_validate(item.owner), created_at=item.created_at,
        secret_detail=item.secret_detail if can_see_secret else None, claim_count=claim_count,
    )


@router.get("/meta/categories")
def categories():
    return CATEGORIES


@router.post("", response_model=ItemOut, status_code=201)
async def create_item(
    kind: ItemKind = Form(...),
    title: str = Form(..., min_length=3, max_length=160),
    description: str = Form(""),
    category: str = Form(...),
    location: str = Form(..., min_length=2, max_length=120),
    event_time: datetime = Form(...),
    secret_detail: str | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if category not in CATEGORIES:
        raise HTTPException(422, f"category must be one of {CATEGORIES}")
    if kind == ItemKind.found and not secret_detail:
        raise HTTPException(422, "Found items need a secret_detail so rightful owners can be verified")
    image_path = await save_image(image) if image and image.filename else None
    item = Item(
        kind=kind, title=title, description=description, category=category, location=location,
        event_time=event_time, secret_detail=secret_detail if kind == ItemKind.found else None,
        image_path=image_path, owner_id=user.id,
    )
    db.add(item)
    db.flush()
    matches = find_matches_for(db, item)
    for m in matches:
        lost_owner = m.lost.owner_id
        notify(db, lost_owner, "match", f"Possible match ({int(m.score * 100)}%) for your lost '{m.lost.title}'",
               link=f"/items/{m.found_id}")
        notify(db, m.found.owner_id, "match", f"Your found '{m.found.title}' may belong to someone",
               link=f"/items/{m.lost_id}")
    audit(db, user.id, "create", "item", item.id, kind=kind.value, matches=len(matches))
    db.commit()
    db.refresh(item)
    return to_out(item, user)


@router.get("", response_model=Page[ItemOut])
def list_items(
    kind: ItemKind | None = None,
    category: str | None = None,
    location: str | None = None,
    status: ItemStatus | None = ItemStatus.open,
    q: str | None = Query(None, max_length=100),
    sort: str = Query("newest", pattern="^(newest|oldest)$"),
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Item).options(joinedload(Item.owner))
    if kind:
        stmt = stmt.where(Item.kind == kind)
    if category:
        stmt = stmt.where(Item.category == category)
    if location:
        stmt = stmt.where(Item.location.ilike(f"%{location}%"))
    if status:
        stmt = stmt.where(Item.status == status)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Item.title.ilike(like), Item.description.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    order = Item.created_at.desc() if sort == "newest" else Item.created_at.asc()
    rows = db.scalars(stmt.order_by(order).offset((page - 1) * size).limit(size)).unique().all()
    return Page(items=[to_out(i, user) for i in rows], total=total or 0, page=page, size=size)


@router.get("/mine", response_model=list[ItemOut])
def my_items(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(
        select(Item).options(joinedload(Item.owner)).where(Item.owner_id == user.id).order_by(Item.created_at.desc())
    ).unique().all()
    return [to_out(i, user, claim_count=len(i.claims)) for i in rows]


@router.get("/matches/mine", response_model=list[MatchOut])
def my_matches(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Matches on items I own, best first. Only matches against still-open items are shown."""
    from app.models import Match

    lost_ids = select(Item.id).where(Item.owner_id == user.id)
    rows = db.scalars(
        select(Match).where(or_(Match.lost_id.in_(lost_ids), Match.found_id.in_(lost_ids)))
        .order_by(Match.score.desc()).limit(50)
    ).all()
    rows = [m for m in rows if m.lost.status == ItemStatus.open and m.found.status == ItemStatus.open]
    return [
        MatchOut(id=m.id, score=m.score, breakdown=m.breakdown, lost=to_out(m.lost, user),
                 found=to_out(m.found, user), created_at=m.created_at)
        for m in rows
    ]


@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return to_out(item, user, claim_count=len(item.claims))


@router.patch("/{item_id}", response_model=ItemOut)
def update_item(item_id: int, body: ItemUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.owner_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Not your item")
    changes = body.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(item, field, value)
    audit(db, user.id, "update", "item", item.id, fields=list(changes))
    db.commit()
    return to_out(item, user)


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    if item.owner_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "Not your item")
    audit(db, user.id, "delete", "item", item.id)
    db.delete(item)
    db.commit()
