# LostFound: Campus Lost & Found Platform

A full-stack platform for reporting lost and found items on a campus. It suggests matches automatically, verifies claims, and pushes real-time notifications.

**Stack:** FastAPI · SQLAlchemy 2 · Alembic · JWT (access + refresh) · WebSockets · React 19 · TypeScript · TanStack Query · Tailwind CSS · Recharts · Docker

## What makes it more than a CRUD board

| Feature | How it works |
|---|---|
| **Match engine** | Every new report is scored against open reports of the opposite kind: 55% text similarity (word + character-trigram TF-IDF cosine, typo tolerant), 20% category, 15% location, 10% timing (an item can't be found before it was lost; score decays over 14 days). Pairs above a threshold are stored with a per-signal breakdown. |
| **Claim verification** | Finders attach a hidden *secret detail* (a scratch, a sticker). Claimants describe it; the answer is scored against the secret and shown to the finder as a verification strength. The secret never leaves the API for non-owners. |
| **Claim workflow** | pending → approved / rejected → returned. Approving auto-rejects competing claims; confirming the handoff awards the finder karma (leaderboard). |
| **Real-time notifications** | Persisted notifications plus a WebSocket push (JWT-authenticated) with client auto-reconnect and backoff. |
| **Auth** | bcrypt, short-lived access tokens, rotating refresh tokens with a single shared in-flight refresh on the client, role-based access, optional email-domain restriction, rate-limited auth endpoints. |
| **Safe uploads** | Images are decoded and validated (not trusted by content-type), downscaled, re-encoded (strips EXIF/GPS) and stored under random names. |
| **Analytics + admin** | Dashboard with trends, category split, hotspots, return rate; admin console with user management and an audit log of every state change. |

## Run locally

```bash
# API
cd backend
python3 -m venv lostfound_env && lostfound_env/bin/python3 -m pip install -r requirements.txt
lostfound_env/bin/alembic upgrade head
lostfound_env/bin/python3 seed.py            # demo data
lostfound_env/bin/uvicorn app.main:app --reload

# Web (new terminal)
cd frontend && npm install && npm run dev    # proxies /api to :8000
```

Demo logins: `admin@lostfound.dev / admin12345`, `riya@lostfound.dev / password123`

Or everything at once: `docker compose up --build`, then open http://localhost:8080.

API docs live at `/docs` (OpenAPI). Tests: `cd backend && lostfound_env/bin/python3 -m pytest`.

## Layout

```
backend/app/
  api/v1/      auth, items, claims, notifications (REST + WS), admin
  services/    matching, similarity, notifications, storage, audit
  models/      SQLAlchemy 2.0 typed models
backend/tests/ matcher unit tests + full lost→found→claim→return flow
frontend/src/  pages/, components/, api client with token refresh
```
