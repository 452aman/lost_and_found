from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1 import admin, auth, claims, items, notifications
from app.core.config import get_settings
from app.db.session import Base, engine
from app import models  # noqa: F401  (register tables)


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)  # Alembic owns prod migrations; this keeps dev/test zero-config
    Path(get_settings().upload_dir).mkdir(exist_ok=True)
    yield


settings = get_settings()
app = FastAPI(title=f"{settings.app_name} API", version="2.0.0", lifespan=lifespan)
app.state.limiter = auth.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

for r in (auth.router, items.router, claims.router, notifications.router, admin.router):
    app.include_router(r, prefix="/api/v1")

Path(settings.upload_dir).mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/health")
def health():
    return {"status": "ok"}
