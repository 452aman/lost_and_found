import asyncio
from collections import defaultdict

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.models import Notification


class ConnectionManager:
    """Tracks live websocket connections per user for push notifications."""

    def __init__(self) -> None:
        self._conns: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._conns[user_id].add(ws)

    def disconnect(self, user_id: int, ws: WebSocket) -> None:
        self._conns[user_id].discard(ws)

    async def push(self, user_id: int, payload: dict) -> None:
        for ws in list(self._conns.get(user_id, ())):
            try:
                await ws.send_json(payload)
            except Exception:  # dead socket; drop it
                self._conns[user_id].discard(ws)


manager = ConnectionManager()


def notify(db: Session, user_id: int, kind: str, message: str, link: str | None = None) -> Notification:
    """Persist a notification and best-effort push it over the websocket."""
    n = Notification(user_id=user_id, kind=kind, message=message, link=link)
    db.add(n)
    db.flush()
    payload = {"id": n.id, "kind": kind, "message": message, "link": link}
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.push(user_id, payload))
    except RuntimeError:
        pass  # called from a sync threadpool worker; clients will poll
    return n
