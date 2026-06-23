from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.wishlist import WishlistStatus


class WishlistItemCreateSchema(BaseModel):
    catalog_variant_id: UUID | None = None
    catalog_request_id: UUID | None = None
    target_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    source_url: HttpUrl | None = None
    priority: int = Field(default=0, ge=0, le=100)
    comment: str | None = None


class WishlistItemUpdateSchema(BaseModel):
    target_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    source_url: HttpUrl | None = None
    priority: int | None = Field(default=None, ge=0, le=100)
    status: WishlistStatus | None = None
    comment: str | None = None


class WishlistItemResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    catalog_variant_id: UUID | None
    catalog_request_id: UUID | None
    target_price: Decimal | None
    currency: str | None
    source_url: str | None
    priority: int
    status: WishlistStatus
    comment: str | None
    created_at: datetime
    updated_at: datetime
