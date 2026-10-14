"""Scores lost/found pairs and persists suggestions above a threshold."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Item, ItemKind, ItemStatus, Match
from app.services.similarity import text_similarity

WEIGHTS = {"text": 0.55, "category": 0.20, "location": 0.15, "time": 0.10}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def time_score(lost_at: datetime, found_at: datetime) -> float:
    """1.0 when found right after being lost, decaying over 14 days.
    An item cannot be found before it was lost, so that scores 0."""
    delta_days = (_aware(found_at) - _aware(lost_at)).total_seconds() / 86400
    if delta_days < -0.5:  # half a day of slack for sloppy timestamps
        return 0.0
    return max(0.0, 1.0 - max(delta_days, 0) / 14)


def score_pair(lost: Item, found: Item) -> tuple[float, dict]:
    parts = {
        "text": text_similarity(f"{lost.title} {lost.description}", f"{found.title} {found.description}"),
        "category": 1.0 if lost.category.lower() == found.category.lower() else 0.0,
        "location": 1.0 if lost.location.lower() == found.location.lower() else
        0.5 * text_similarity(lost.location, found.location),
        "time": time_score(lost.event_time, found.event_time),
    }
    total = sum(WEIGHTS[k] * v for k, v in parts.items())
    return round(total, 4), {k: round(v, 3) for k, v in parts.items()}


def find_matches_for(db: Session, item: Item) -> list[Match]:
    """Compare a new item against open items of the opposite kind."""
    other_kind = ItemKind.found if item.kind == ItemKind.lost else ItemKind.lost
    candidates = db.scalars(
        select(Item).where(Item.kind == other_kind, Item.status == ItemStatus.open, Item.owner_id != item.owner_id)
    ).all()
    threshold = get_settings().match_threshold
    created: list[Match] = []
    for other in candidates:
        lost, found = (item, other) if item.kind == ItemKind.lost else (other, item)
        score, breakdown = score_pair(lost, found)
        if score < threshold:
            continue
        exists = db.scalar(select(Match).where(Match.lost_id == lost.id, Match.found_id == found.id))
        if exists:
            continue
        m = Match(lost_id=lost.id, found_id=found.id, score=score, breakdown=breakdown)
        db.add(m)
        created.append(m)
    db.flush()
    return created
