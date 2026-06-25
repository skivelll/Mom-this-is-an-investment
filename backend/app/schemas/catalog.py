from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.item import CatalogStatus


class CatalogItemCreateSchema(BaseModel):
    category_id: UUID
    canonical_title: str = Field(min_length=1, max_length=500)
    normalized_title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    release_year: int | None = Field(default=None, ge=1800, le=3000)
    status: CatalogStatus = CatalogStatus.ACTIVE


class CatalogVariantCreateSchema(BaseModel):
    catalog_item_id: UUID
    canonical_title: str = Field(min_length=1, max_length=500)
    normalized_title: str = Field(min_length=1, max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)
    release_date: date | None = None
    status: CatalogStatus = CatalogStatus.ACTIVE


class CatalogItemResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    canonical_title: str
    normalized_title: str
    description: str | None
    release_year: int | None
    status: CatalogStatus
    created_by_id: UUID
    updated_by_id: UUID | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None


class CatalogVariantResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    catalog_item_id: UUID
    canonical_title: str
    normalized_title: str
    sku: str | None
    barcode: str | None
    release_date: date | None
    status: CatalogStatus
    created_by_id: UUID
    updated_by_id: UUID | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
    item_title: str | None = None
    variant_label: str | None = None
    primary_image_url: str | None = None
