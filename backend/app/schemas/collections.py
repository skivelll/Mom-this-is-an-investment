from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.collections import CollectionVisibility, ItemCondition


class CollectionCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    visibility: CollectionVisibility = CollectionVisibility.PRIVATE


class CollectionUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    visibility: CollectionVisibility | None = None


class CollectionResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    name: str
    description: str | None
    visibility: CollectionVisibility
    created_at: datetime
    updated_at: datetime


class CollectionItemCreateSchema(BaseModel):
    catalog_variant_id: UUID
    condition: ItemCondition | None = None
    quantity: int = Field(default=1, ge=1)
    purchase_price: Decimal | None = Field(default=None, ge=0)
    purchase_currency: str | None = Field(default=None, min_length=3, max_length=3)
    purchase_date: date | None = None
    comment: str | None = None


class CollectionItemResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    collection_id: UUID
    catalog_variant_id: UUID
    condition: ItemCondition | None
    quantity: int
    purchase_price: Decimal | None
    purchase_currency: str | None
    purchase_date: date | None
    comment: str | None
    created_at: datetime
    updated_at: datetime
