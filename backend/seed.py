"""Populate a dev database with demo users and items:  python seed.py"""
from datetime import datetime, timedelta, timezone

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models import Item, ItemKind, Role, User
from app.services.matching import find_matches_for

Base.metadata.create_all(engine)
now = datetime.now(timezone.utc)

with SessionLocal() as db:
    if db.query(User).count():
        raise SystemExit("Database already has data; delete lostfound.db to reseed.")
    admin = User(email="admin@lostfound.dev", name="Admin", role=Role.admin, hashed_password=hash_password("admin12345"))
    riya = User(email="riya@lostfound.dev", name="Riya Sharma", hashed_password=hash_password("password123"))
    arjun = User(email="arjun@lostfound.dev", name="Arjun Mehta", hashed_password=hash_password("password123"))
    db.add_all([admin, riya, arjun])
    db.flush()
    rows = [
        (riya, ItemKind.lost, "Black Dell laptop", "Black Dell laptop with cat sticker on the lid", "electronics", "Central Library", 30, None),
        (arjun, ItemKind.found, "Dell laptop (black)", "Found a black Dell laptop with stickers near the reading hall", "electronics", "Central Library", 26, "Cracked bottom-left corner"),
        (riya, ItemKind.lost, "Blue water bottle", "Steel blue bottle with dent", "other", "Cricket Ground", 70, None),
        (arjun, ItemKind.found, "Hostel room keys", "Three keys on a red ring", "keys", "Rajendra Bhawan", 50, "Keyring has a small Mickey Mouse charm"),
        (riya, ItemKind.lost, "Student ID card", "ID card in a transparent holder", "documents", "Main Gate", 90, None),
    ]
    for owner, kind, title, desc, cat, loc, hrs, secret in rows:
        it = Item(kind=kind, title=title, description=desc, category=cat, location=loc,
                  event_time=now - timedelta(hours=hrs), secret_detail=secret, owner_id=owner.id)
        db.add(it)
        db.flush()
        find_matches_for(db, it)
    db.commit()
    print("Seeded. Admin: admin@lostfound.dev / admin12345  |  Student: riya@lostfound.dev / password123")
