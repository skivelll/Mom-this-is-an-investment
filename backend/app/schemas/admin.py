from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.category import AttributeValueType
from app.models.reference import ReferenceType


class CategoryCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = True


class CategoryResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AttributeDefinitionCreateSchema(BaseModel):
    category_id: UUID
    code: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    value_type: AttributeValueType
    is_required: bool = False
    is_filterable: bool = False
    is_searchable: bool = False
    is_variant_attribute: bool = False
    sort_order: int = 0
    validation_rules: dict[str, Any] | None = None


class AttributeDefinitionResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    code: str
    name: str
    value_type: AttributeValueType
    is_required: bool
    is_filterable: bool
    is_searchable: bool
    is_variant_attribute: bool
    sort_order: int
    validation_rules: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime


class ReferenceEntityCreateSchema(BaseModel):
    type: ReferenceType
    canonical_name: str = Field(min_length=1, max_length=255)
    normalized_name: str = Field(min_length=1, max_length=255)


class ReferenceEntityResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: ReferenceType
    canonical_name: str
    normalized_name: str
    created_at: datetime
    updated_at: datetime
