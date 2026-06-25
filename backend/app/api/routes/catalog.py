from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.item import CatalogItem
from app.models.user import User
from app.models.variant import CatalogVariant
from app.schemas.catalog import (
    CatalogItemCreateSchema,
    CatalogItemResponseSchema,
    CatalogVariantCreateSchema,
    CatalogVariantResponseSchema,
)
from app.services.catalog import (
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
    return [CatalogItemResponseSchema.model_validate(item) for item in items]


@router.get("/items/{item_id}", response_model=CatalogItemResponseSchema)
async def get_catalog_item(
    item_id: UUID,
    session: DbSession,
) -> CatalogItemResponseSchema:
    service = CatalogService(session)
    item = await service.get_item(item_id)
    return CatalogItemResponseSchema.model_validate(item)


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
        ),
    )
    return CatalogItemResponseSchema.model_validate(item)


@router.get("/variants", response_model=list[CatalogVariantResponseSchema])
async def search_catalog_variants(
    session: DbSession,
    query: Annotated[str | None, Query(min_length=1)] = None,
    category_id: UUID | None = None,
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

    rows = await session.execute(statement)
    row_values = rows.all()
    primary_urls = await primary_image_urls_by_variant(
        session,
        variant_item_ids={variant.id: catalog_item.id for variant, catalog_item in row_values},
    )
    return [
        _variant_response_schema(
            variant=variant,
            catalog_item=catalog_item,
            primary_image_url=primary_urls.get(variant.id),
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
    return _variant_response_schema(
        variant=variant,
        catalog_item=catalog_item,
        primary_image_url=primary_urls.get(variant.id),
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
        ),
    )
    return CatalogVariantResponseSchema.model_validate(variant)


def _variant_response_schema(
    *,
    variant: CatalogVariant,
    catalog_item: CatalogItem,
    primary_image_url: str | None = None,
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
