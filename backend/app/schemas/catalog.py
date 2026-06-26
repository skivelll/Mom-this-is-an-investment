from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.category import AttributeValueType
from app.models.item import CatalogStatus
from app.models.reference import ReferenceType


class CatalogAttributeValueInputSchema(BaseModel):
    attribute_definition_id: UUID
    value_text: str | None = Field(default=None, max_length=1000)
    value_integer: int | None = None
    value_decimal: Decimal | None = None
    value_boolean: bool | None = None
    value_date: date | None = None
    reference_entity_id: UUID | None = None


class CatalogAttributeValueResponseSchema(BaseModel):
    id: UUID
    attribute_definition_id: UUID
    code: str
    name: str
    value_type: AttributeValueType
    reference_type: ReferenceType | None
    is_variant_attribute: bool
    value_text: str | None
    value_integer: int | None
    value_decimal: Decimal | None
    value_boolean: bool | None
    value_date: date | None
    reference_entity_id: UUID | None
    reference_label: str | None = None
    display_value: str | None = None


class CatalogItemCreateSchema(BaseModel):
    category_id: UUID
    canonical_title: str = Field(min_length=1, max_length=500)
    normalized_title: str = Field(min_length=1, max_length=500)
    description: str | None = None
    release_year: int | None = Field(default=None, ge=1800, le=3000)
    status: CatalogStatus = CatalogStatus.ACTIVE
    attributes: list[CatalogAttributeValueInputSchema] = Field(default_factory=list)


class CatalogVariantCreateSchema(BaseModel):
    catalog_item_id: UUID
    canonical_title: str = Field(min_length=1, max_length=500)
    normalized_title: str = Field(min_length=1, max_length=500)
    sku: str | None = Field(default=None, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)
    release_date: date | None = None
    status: CatalogStatus = CatalogStatus.ACTIVE
    attributes: list[CatalogAttributeValueInputSchema] = Field(default_factory=list)


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
    attributes: list[CatalogAttributeValueResponseSchema] = Field(default_factory=list)


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
    attributes: list[CatalogAttributeValueResponseSchema] = Field(default_factory=list)
