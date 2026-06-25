from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.collections import Collection, CollectionItem
from app.models.item import CatalogItem
from app.models.user import User
from app.models.variant import CatalogVariant
from app.schemas.collections import (
    CollectionCreateSchema,
    CollectionItemCreateSchema,
    CollectionItemDetailedResponseSchema,
    CollectionItemResponseSchema,
    CollectionItemUpdateSchema,
    CollectionResponseSchema,
    CollectionUpdateSchema,
)
from app.services.collections import (
    AddCollectionItemCommand,
    CollectionService,
    CreateCollectionCommand,
    UpdateCollectionCommand,
    UpdateCollectionItemCommand,
)
from app.services.media import primary_image_urls_by_variant

router = APIRouter(prefix="/collections", tags=["collections"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("", response_model=list[CollectionResponseSchema])
async def list_collections(
    current_user: CurrentUser,
    session: DbSession,
) -> list[CollectionResponseSchema]:
    service = CollectionService(session)
    collections = await service.list_collections(user=current_user)
    return [CollectionResponseSchema.model_validate(collection) for collection in collections]


@router.post("", response_model=CollectionResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_collection(
    payload: CollectionCreateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CollectionResponseSchema:
    service = CollectionService(session)
    collection = await service.create_collection(
        user=current_user,
        command=CreateCollectionCommand(
            name=payload.name,
            description=payload.description,
            visibility=payload.visibility,
        ),
    )
    await session.refresh(collection)
    return CollectionResponseSchema.model_validate(collection)


@router.get("/items", response_model=list[CollectionItemDetailedResponseSchema])
async def list_all_collection_items(
    current_user: CurrentUser,
    session: DbSession,
    collection_id: UUID | None = None,
    query: Annotated[str | None, Query(min_length=1)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CollectionItemDetailedResponseSchema]:
    statement = (
        select(CollectionItem, Collection.name, CatalogVariant, CatalogItem)
        .join(Collection, CollectionItem.collection_id == Collection.id)
        .join(CatalogVariant, CollectionItem.catalog_variant_id == CatalogVariant.id)
        .join(CatalogItem, CatalogVariant.catalog_item_id == CatalogItem.id)
        .where(Collection.owner_id == current_user.id)
        .order_by(CollectionItem.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if collection_id is not None:
        statement = statement.where(CollectionItem.collection_id == collection_id)
    if query:
        pattern = f"%{query}%"
        statement = statement.where(
            or_(
                CatalogItem.canonical_title.ilike(pattern),
                CatalogItem.normalized_title.ilike(pattern),
                CatalogVariant.canonical_title.ilike(pattern),
                CatalogVariant.normalized_title.ilike(pattern),
            ),
        )

    rows = await session.execute(statement)
    row_values = rows.all()
    primary_urls = await primary_image_urls_by_variant(
        session,
        variant_item_ids={
            variant.id: catalog_item.id for _, _, variant, catalog_item in row_values
        },
    )
    return [
        _collection_item_detail_schema(
            item=item,
            collection_name=collection_name,
            variant=variant,
            catalog_item=catalog_item,
            primary_image_url=primary_urls.get(variant.id),
        )
        for item, collection_name, variant, catalog_item in row_values
    ]


@router.get("/{collection_id}", response_model=CollectionResponseSchema)
async def get_collection(
    collection_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> CollectionResponseSchema:
    service = CollectionService(session)
    collection = await service.get_collection(user=current_user, collection_id=collection_id)
    return CollectionResponseSchema.model_validate(collection)


@router.patch("/{collection_id}", response_model=CollectionResponseSchema)
async def update_collection(
    collection_id: UUID,
    payload: CollectionUpdateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CollectionResponseSchema:
    service = CollectionService(session)
    collection = await service.update_collection(
        user=current_user,
        collection_id=collection_id,
        command=UpdateCollectionCommand(
            name=payload.name,
            description=payload.description,
            visibility=payload.visibility,
        ),
    )
    await session.refresh(collection)
    return CollectionResponseSchema.model_validate(collection)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> Response:
    service = CollectionService(session)
    await service.delete_collection(user=current_user, collection_id=collection_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{collection_id}/items", response_model=list[CollectionItemResponseSchema])
async def list_collection_items(
    collection_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> list[CollectionItemResponseSchema]:
    service = CollectionService(session)
    items = await service.list_items(user=current_user, collection_id=collection_id)
    return [CollectionItemResponseSchema.model_validate(item) for item in items]


@router.post(
    "/{collection_id}/items",
    response_model=CollectionItemResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_collection_item(
    collection_id: UUID,
    payload: CollectionItemCreateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CollectionItemResponseSchema:
    service = CollectionService(session)
    item = await service.add_item(
        user=current_user,
        collection_id=collection_id,
        command=AddCollectionItemCommand(
            catalog_variant_id=payload.catalog_variant_id,
            condition=payload.condition,
            quantity=payload.quantity,
            purchase_price=payload.purchase_price,
            purchase_currency=payload.purchase_currency,
            purchase_date=payload.purchase_date,
            comment=payload.comment,
        ),
    )
    await session.refresh(item)
    return CollectionItemResponseSchema.model_validate(item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection_item(
    item_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> Response:
    service = CollectionService(session)
    await service.delete_item(user=current_user, item_id=item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/items/{item_id}", response_model=CollectionItemResponseSchema)
async def update_collection_item(
    item_id: UUID,
    payload: CollectionItemUpdateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CollectionItemResponseSchema:
    service = CollectionService(session)
    item = await service.update_item(
        user=current_user,
        item_id=item_id,
        command=UpdateCollectionItemCommand(values=payload.model_dump(exclude_unset=True)),
    )
    await session.refresh(item)
    return CollectionItemResponseSchema.model_validate(item)


def _collection_item_detail_schema(
    *,
    item: CollectionItem,
    collection_name: str,
    variant: CatalogVariant,
    catalog_item: CatalogItem,
    primary_image_url: str | None = None,
) -> CollectionItemDetailedResponseSchema:
    return CollectionItemDetailedResponseSchema(
        id=item.id,
        collection_id=item.collection_id,
        collection_name=collection_name,
        catalog_variant_id=item.catalog_variant_id,
        catalog_item_id=catalog_item.id,
        item_title=catalog_item.canonical_title,
        variant_title=variant.canonical_title,
        variant_label=_variant_label(item_title=catalog_item.canonical_title, variant=variant),
        primary_image_url=primary_image_url,
        condition=item.condition,
        quantity=item.quantity,
        purchase_price=item.purchase_price,
        purchase_currency=item.purchase_currency,
        purchase_date=item.purchase_date,
        comment=item.comment,
        created_at=item.created_at,
        updated_at=item.updated_at,
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
