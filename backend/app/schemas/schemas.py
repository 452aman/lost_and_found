from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import ClaimStatus, ItemKind, ItemStatus, Role

T = TypeVar("T")


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int


# ---- auth / users
class RegisterIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserOut(ORM):
    id: int
    email: EmailStr
    name: str
    role: Role
    karma: int
    is_active: bool
    created_at: datetime


class UserPublic(ORM):
    id: int
    name: str
    karma: int


# ---- items
class ItemOut(ORM):
    id: int
    kind: ItemKind
    status: ItemStatus
    title: str
    description: str
    category: str
    location: str
    event_time: datetime
    image_url: str | None = None
    owner: UserPublic
    created_at: datetime
    secret_detail: str | None = None  # populated only for the owner / admins
    claim_count: int = 0


class ItemUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=160)
    description: str | None = None
    category: str | None = None
    location: str | None = None
    status: ItemStatus | None = None


# ---- matches
class MatchOut(ORM):
    id: int
    score: float
    breakdown: dict
    lost: ItemOut
    found: ItemOut
    created_at: datetime


# ---- claims
class ClaimIn(BaseModel):
    answer: str = Field(min_length=5, max_length=1000, description="Describe the hidden detail of the item")


class ClaimDecision(BaseModel):
    approve: bool
    note: str | None = Field(default=None, max_length=500)


class ClaimOut(ORM):
    id: int
    item_id: int
    item_title: str
    claimant: UserPublic
    answer: str
    verification_score: float
    status: ClaimStatus
    reviewer_note: str | None
    created_at: datetime
    resolved_at: datetime | None


# ---- notifications / admin
class NotificationOut(ORM):
    id: int
    kind: str
    message: str
    link: str | None
    read: bool
    created_at: datetime


class AuditOut(ORM):
    id: int
    actor_id: int | None
    action: str
    entity: str
    entity_id: int | None
    detail: dict
    created_at: datetime


class StatsOut(BaseModel):
    total_items: int
    open_lost: int
    open_found: int
    returned: int
    pending_claims: int
    return_rate: float
    by_category: dict[str, int]
    by_location: dict[str, int]
    daily: list[dict]
