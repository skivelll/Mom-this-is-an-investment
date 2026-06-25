from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.media import CatalogMediaType


class CatalogMediaUploadRequestSchema(BaseModel):
    catalog_item_id: UUID
    catalog_variant_id: UUID | None = None
    original_filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0)


class CatalogMediaUploadResponseSchema(BaseModel):
    object_key: str
    upload_url: str
    public_url: str
    headers: dict[str, str]
    expires_in: int


class CatalogMediaConfirmSchema(BaseModel):
    catalog_item_id: UUID
    catalog_variant_id: UUID | None = None
    object_key: str = Field(min_length=1, max_length=1024)
    original_filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=100)
    size_bytes: int = Field(gt=0)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    is_primary: bool = False
    sort_order: int = 0
    alt_text: str | None = None


class CatalogMediaUpdateSchema(BaseModel):
    is_primary: bool | None = None
    sort_order: int | None = None
    alt_text: str | None = None


class CatalogMediaResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    catalog_item_id: UUID
    catalog_variant_id: UUID | None
    object_key: str
    url: str
    original_filename: str
    mime_type: str
    size_bytes: int
    width: int | None
    height: int | None
    media_type: CatalogMediaType
    is_primary: bool
    sort_order: int
    alt_text: str | None
    created_at: datetime
    updated_at: datetime
