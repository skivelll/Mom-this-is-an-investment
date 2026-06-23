from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.item import CatalogStatus
from app.models.request import CatalogRequestStatus
from app.models.wishlist import WishlistStatus


class WishlistDraftSchema(BaseModel):
    target_price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    source_url: HttpUrl | None = None
    priority: int = Field(default=0, ge=0, le=100)
    comment: str | None = None


class CatalogRequestCreateSchema(BaseModel):
    category_id: UUID
    raw_title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    source_url: HttpUrl | None = None
    proposed_data: dict[str, Any] | None = None
    wishlist: WishlistDraftSchema | None = None


class CatalogItemDraftSchema(BaseModel):
    category_id: UUID
    canonical_title: str = Field(min_length=1, max_length=500)
    normalized_title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    release_year: int | None = Field(default=None, ge=1800, le=3000)
    status: CatalogStatus = CatalogStatus.ACTIVE


class CatalogVariantDraftSchema(BaseModel):
    canonical_title: str = Field(min_length=1, max_length=500)
    normalized_title: str = Field(min_length=1, max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)
    release_date: date | None = None
    status: CatalogStatus = CatalogStatus.ACTIVE


class CatalogRequestApproveSchema(BaseModel):
    existing_catalog_item_id: UUID | None = None
    existing_variant_id: UUID | None = None
    new_catalog_item: CatalogItemDraftSchema | None = None
    new_variant: CatalogVariantDraftSchema | None = None
    comment: str | None = None
    payload: dict[str, Any] | None = None


class CatalogRequestRejectSchema(BaseModel):
    reason: str = Field(min_length=1)
    comment: str | None = None
    payload: dict[str, Any] | None = None


class CatalogRequestDuplicateSchema(BaseModel):
    existing_variant_id: UUID
    comment: str | None = None
    payload: dict[str, Any] | None = None


class CatalogRequestResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by_id: UUID
    category_id: UUID
    raw_title: str
    description: str | None
    source_url: str | None
    proposed_data: dict[str, Any] | None
    status: CatalogRequestStatus
    assigned_to_id: UUID | None
    moderated_by_id: UUID | None
    rejection_reason: str | None
    approved_catalog_item_id: UUID | None
    approved_variant_id: UUID | None
    created_at: datetime
    updated_at: datetime


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


class CatalogRequestCreateResponseSchema(BaseModel):
    request: CatalogRequestResponseSchema
    wishlist_item: WishlistItemResponseSchema | None
