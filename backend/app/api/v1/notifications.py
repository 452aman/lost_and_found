import jwt
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import decode_token
from app.db.session import SessionLocal, get_db
from app.models import Notification, User
from app.schemas.schemas import NotificationOut
from app.services.notifications import manager

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(unread_only: bool = False, limit: int = Query(30, le=100),
                       db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stmt = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        stmt = stmt.where(Notification.read.is_(False))
    return db.scalars(stmt.order_by(Notification.created_at.desc()).limit(limit)).all()


@router.get("/notifications/unread-count")
def unread_count(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.scalar(select(func.count()).select_from(Notification).where(
        Notification.user_id == user.id, Notification.read.is_(False)))
    return {"count": n or 0}


@router.post("/notifications/read-all", status_code=204)
def read_all(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.execute(update(Notification).where(Notification.user_id == user.id).values(read=True))
    db.commit()


@router.websocket("/ws/notifications")
async def notifications_ws(ws: WebSocket, token: str):
    try:
        user_id = decode_token(token, "access")
    except jwt.PyJWTError:
        await ws.close(code=4401)
        return
    with SessionLocal() as db:
        if not db.get(User, user_id):
            await ws.close(code=4401)
            return
    await manager.connect(user_id, ws)
    try:
        while True:
            await ws.receive_text()  # keep-alive pings from the client
    except WebSocketDisconnect:
        manager.disconnect(user_id, ws)
