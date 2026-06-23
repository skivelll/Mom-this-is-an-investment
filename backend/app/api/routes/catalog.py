from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.user import User
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
    service = CatalogService(session)
    variants = await service.search_variants(
        query=query,
        category_id=category_id,
        limit=limit,
        offset=offset,
    )
    return [CatalogVariantResponseSchema.model_validate(variant) for variant in variants]


@router.get("/variants/{variant_id}", response_model=CatalogVariantResponseSchema)
async def get_catalog_variant(
    variant_id: UUID,
    session: DbSession,
) -> CatalogVariantResponseSchema:
    service = CatalogService(session)
    variant = await service.get_variant(variant_id)
    return CatalogVariantResponseSchema.model_validate(variant)


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
