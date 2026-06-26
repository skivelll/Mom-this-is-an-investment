from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.attribute import CatalogItemAttribute, CatalogVariantAttribute
from app.models.category import AttributeDefinition
from app.models.item import CatalogItem
from app.models.reference import ReferenceEntity
from app.models.user import User
from app.models.variant import CatalogVariant
from app.schemas.catalog import (
    CatalogAttributeValueInputSchema,
    CatalogAttributeValueResponseSchema,
    CatalogItemCreateSchema,
    CatalogItemResponseSchema,
    CatalogVariantCreateSchema,
    CatalogVariantResponseSchema,
)
from app.services.catalog import (
    CatalogAttributeValueCommand,
    CatalogService,
    CreateCatalogItemCommand,
    CreateCatalogVariantCommand,
)
from app.services.media import primary_image_urls_by_variant

router = APIRouter(prefix="/catalog", tags=["catalog"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("/items", response_model=list[CatalogItemResponseSchema])
async def search_catalog_items(
    session: DbSession,
    query: Annotated[str | None, Query(min_length=1)] = None,
    category_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CatalogItemResponseSchema]:
    service = CatalogService(session)
    items = await service.search_items(
        query=query,
        category_id=category_id,
        limit=limit,
        offset=offset,
    )
    attributes = await _item_attributes_by_item(session, item_ids={item.id for item in items})
    return [
        _item_response_schema(item=item, attributes=attributes.get(item.id, [])) for item in items
    ]


@router.get("/items/{item_id}", response_model=CatalogItemResponseSchema)
async def get_catalog_item(
    item_id: UUID,
    session: DbSession,
) -> CatalogItemResponseSchema:
    service = CatalogService(session)
    item = await service.get_item(item_id)
    attributes = await _item_attributes_by_item(session, item_ids={item.id})
    return _item_response_schema(item=item, attributes=attributes.get(item.id, []))


@router.post(
    "/items",
    response_model=CatalogItemResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_catalog_item(
    payload: CatalogItemCreateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CatalogItemResponseSchema:
    service = CatalogService(session)
    item = await service.create_item(
        actor=current_user,
        command=CreateCatalogItemCommand(
            category_id=payload.category_id,
            canonical_title=payload.canonical_title,
            normalized_title=payload.normalized_title,
            description=payload.description,
            release_year=payload.release_year,
            status=payload.status,
            attributes=_attribute_commands(payload.attributes),
        ),
    )
    attributes = await _item_attributes_by_item(session, item_ids={item.id})
    return _item_response_schema(item=item, attributes=attributes.get(item.id, []))


@router.get("/variants", response_model=list[CatalogVariantResponseSchema])
async def search_catalog_variants(
    session: DbSession,
    query: Annotated[str | None, Query(min_length=1)] = None,
    category_id: UUID | None = None,
    catalog_item_id: UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CatalogVariantResponseSchema]:
    statement = (
        select(CatalogVariant, CatalogItem)
        .join(CatalogItem, CatalogVariant.catalog_item_id == CatalogItem.id)
        .order_by(CatalogItem.canonical_title.asc(), CatalogVariant.canonical_title.asc())
        .limit(limit)
        .offset(offset)
    )
    if query:
        pattern = f"%{query}%"
        statement = statement.where(
            or_(
                CatalogVariant.canonical_title.ilike(pattern),
                CatalogVariant.normalized_title.ilike(pattern),
                CatalogItem.canonical_title.ilike(pattern),
                CatalogItem.normalized_title.ilike(pattern),
            ),
        )
    if category_id is not None:
        statement = statement.where(CatalogItem.category_id == category_id)
    if catalog_item_id is not None:
        statement = statement.where(CatalogVariant.catalog_item_id == catalog_item_id)

    rows = await session.execute(statement)
    row_values = rows.all()
    primary_urls = await primary_image_urls_by_variant(
        session,
        variant_item_ids={variant.id: catalog_item.id for variant, catalog_item in row_values},
    )
    attributes = await _variant_attributes_by_variant(
        session,
        variant_ids={variant.id for variant, _ in row_values},
    )
    return [
        _variant_response_schema(
            variant=variant,
            catalog_item=catalog_item,
            primary_image_url=primary_urls.get(variant.id),
            attributes=attributes.get(variant.id, []),
        )
        for variant, catalog_item in row_values
    ]


@router.get("/variants/{variant_id}", response_model=CatalogVariantResponseSchema)
async def get_catalog_variant(
    variant_id: UUID,
    session: DbSession,
) -> CatalogVariantResponseSchema:
    statement = (
        select(CatalogVariant, CatalogItem)
        .join(CatalogItem, CatalogVariant.catalog_item_id == CatalogItem.id)
        .where(CatalogVariant.id == variant_id)
    )
    result = await session.execute(statement)
    row = result.one_or_none()
    if row is None:
        service = CatalogService(session)
        variant = await service.get_variant(variant_id)
        return CatalogVariantResponseSchema.model_validate(variant)
    variant, catalog_item = row
    primary_urls = await primary_image_urls_by_variant(
        session,
        variant_item_ids={variant.id: catalog_item.id},
    )
    attributes = await _variant_attributes_by_variant(session, variant_ids={variant.id})
    return _variant_response_schema(
        variant=variant,
        catalog_item=catalog_item,
        primary_image_url=primary_urls.get(variant.id),
        attributes=attributes.get(variant.id, []),
    )


@router.post(
    "/variants",
    response_model=CatalogVariantResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_catalog_variant(
    payload: CatalogVariantCreateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CatalogVariantResponseSchema:
    service = CatalogService(session)
    variant = await service.create_variant(
        actor=current_user,
        command=CreateCatalogVariantCommand(
            catalog_item_id=payload.catalog_item_id,
            canonical_title=payload.canonical_title,
            normalized_title=payload.normalized_title,
            sku=payload.sku,
            barcode=payload.barcode,
            release_date=payload.release_date,
            status=payload.status,
            attributes=_attribute_commands(payload.attributes),
        ),
    )
    statement = select(CatalogItem).where(CatalogItem.id == variant.catalog_item_id)
    catalog_item = (await session.execute(statement)).scalar_one()
    attributes = await _variant_attributes_by_variant(session, variant_ids={variant.id})
    return _variant_response_schema(
        variant=variant,
        catalog_item=catalog_item,
        attributes=attributes.get(variant.id, []),
    )


def _item_response_schema(
    *,
    item: CatalogItem,
    attributes: list[CatalogAttributeValueResponseSchema],
) -> CatalogItemResponseSchema:
    return CatalogItemResponseSchema(
        id=item.id,
        category_id=item.category_id,
        canonical_title=item.canonical_title,
        normalized_title=item.normalized_title,
        description=item.description,
        release_year=item.release_year,
        status=item.status,
        created_by_id=item.created_by_id,
        updated_by_id=item.updated_by_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
        deleted_at=item.deleted_at,
        attributes=attributes,
    )


def _variant_response_schema(
    *,
    variant: CatalogVariant,
    catalog_item: CatalogItem,
    primary_image_url: str | None = None,
    attributes: list[CatalogAttributeValueResponseSchema] | None = None,
) -> CatalogVariantResponseSchema:
    return CatalogVariantResponseSchema(
        id=variant.id,
        catalog_item_id=variant.catalog_item_id,
        canonical_title=variant.canonical_title,
        normalized_title=variant.normalized_title,
        sku=variant.sku,
        barcode=variant.barcode,
        release_date=variant.release_date,
        status=variant.status,
        created_by_id=variant.created_by_id,
        updated_by_id=variant.updated_by_id,
        created_at=variant.created_at,
        updated_at=variant.updated_at,
        deleted_at=variant.deleted_at,
        item_title=catalog_item.canonical_title,
        variant_label=_variant_label(item_title=catalog_item.canonical_title, variant=variant),
        primary_image_url=primary_image_url,
        attributes=attributes or [],
    )


def _attribute_commands(
    values: list[CatalogAttributeValueInputSchema],
) -> list[CatalogAttributeValueCommand]:
    return [
        CatalogAttributeValueCommand(
            attribute_definition_id=value.attribute_definition_id,
            value_text=value.value_text,
            value_integer=value.value_integer,
            value_decimal=value.value_decimal,
            value_boolean=value.value_boolean,
            value_date=value.value_date,
            reference_entity_id=value.reference_entity_id,
        )
        for value in values
    ]


async def _item_attributes_by_item(
    session: AsyncSession,
    *,
    item_ids: set[UUID],
) -> dict[UUID, list[CatalogAttributeValueResponseSchema]]:
    if not item_ids:
        return {}
    statement = (
        select(CatalogItemAttribute, AttributeDefinition, ReferenceEntity)
        .join(
            AttributeDefinition,
            CatalogItemAttribute.attribute_definition_id == AttributeDefinition.id,
        )
        .outerjoin(ReferenceEntity, CatalogItemAttribute.reference_entity_id == ReferenceEntity.id)
        .where(CatalogItemAttribute.catalog_item_id.in_(item_ids))
        .order_by(AttributeDefinition.sort_order.asc(), AttributeDefinition.code.asc())
    )
    rows = await session.execute(statement)
    result: dict[UUID, list[CatalogAttributeValueResponseSchema]] = {}
    for value, definition, reference in rows.all():
        result.setdefault(value.catalog_item_id, []).append(
            _attribute_response(value=value, definition=definition, reference=reference)
        )
    return result


async def _variant_attributes_by_variant(
    session: AsyncSession,
    *,
    variant_ids: set[UUID],
) -> dict[UUID, list[CatalogAttributeValueResponseSchema]]:
    if not variant_ids:
        return {}
    statement = (
        select(CatalogVariantAttribute, AttributeDefinition, ReferenceEntity)
        .join(
            AttributeDefinition,
            CatalogVariantAttribute.attribute_definition_id == AttributeDefinition.id,
        )
        .outerjoin(
            ReferenceEntity,
            CatalogVariantAttribute.reference_entity_id == ReferenceEntity.id,
        )
        .where(CatalogVariantAttribute.catalog_variant_id.in_(variant_ids))
        .order_by(AttributeDefinition.sort_order.asc(), AttributeDefinition.code.asc())
    )
    rows = await session.execute(statement)
    result: dict[UUID, list[CatalogAttributeValueResponseSchema]] = {}
    for value, definition, reference in rows.all():
        result.setdefault(value.catalog_variant_id, []).append(
            _attribute_response(value=value, definition=definition, reference=reference)
        )
    return result


def _attribute_response(
    *,
    value: CatalogItemAttribute | CatalogVariantAttribute,
    definition: AttributeDefinition,
    reference: ReferenceEntity | None,
) -> CatalogAttributeValueResponseSchema:
    display_value = (
        value.value_text
        if value.value_text is not None
        else str(value.value_integer)
        if value.value_integer is not None
        else str(value.value_decimal)
        if value.value_decimal is not None
        else "Да"
        if value.value_boolean is True
        else "Нет"
        if value.value_boolean is False
        else value.value_date.isoformat()
        if value.value_date is not None
        else reference.canonical_name
        if reference is not None
        else None
    )
    return CatalogAttributeValueResponseSchema(
        id=value.id,
        attribute_definition_id=definition.id,
        code=definition.code,
        name=definition.name,
        value_type=definition.value_type,
        reference_type=definition.reference_type,
        is_variant_attribute=definition.is_variant_attribute,
        value_text=value.value_text,
        value_integer=value.value_integer,
        value_decimal=value.value_decimal,
        value_boolean=value.value_boolean,
        value_date=value.value_date,
        reference_entity_id=value.reference_entity_id,
        reference_label=reference.canonical_name if reference is not None else None,
        display_value=display_value,
    )


def _variant_label(*, item_title: str, variant: CatalogVariant) -> str | None:
    parts: list[str] = []
    if variant.canonical_title.strip().lower() != item_title.strip().lower():
        parts.append(variant.canonical_title)
    if variant.release_date is not None:
        year = str(variant.release_date.year)
        if not any(year in part for part in parts):
            parts.append(year)
    return ", ".join(parts) or None
