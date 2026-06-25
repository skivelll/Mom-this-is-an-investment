from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.item import CatalogItem
from app.models.request import CatalogRequest
from app.models.user import User
from app.models.variant import CatalogVariant
from app.models.wishlist import WishlistItem, WishlistStatus
from app.schemas.wishlist import (
    WishlistItemCreateSchema,
    WishlistItemDetailedResponseSchema,
    WishlistItemResponseSchema,
    WishlistItemUpdateSchema,
)
from app.services.wishlist import (
    CreateWishlistItemCommand,
    UpdateWishlistItemCommand,
    WishlistService,
)

router = APIRouter(prefix="/wishlist", tags=["wishlist"])

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.get("", response_model=list[WishlistItemResponseSchema])
async def list_wishlist(
    current_user: CurrentUser,
    session: DbSession,
) -> list[WishlistItemResponseSchema]:
    service = WishlistService(session)
    items = await service.list_items(user=current_user)
    return [WishlistItemResponseSchema.model_validate(item) for item in items]


@router.get("/detailed", response_model=list[WishlistItemDetailedResponseSchema])
async def list_wishlist_detailed(
    current_user: CurrentUser,
    session: DbSession,
    item_status: Annotated[WishlistStatus | None, Query(alias="status")] = None,
    query: Annotated[str | None, Query(min_length=1)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[WishlistItemDetailedResponseSchema]:
    statement = (
        select(WishlistItem, CatalogVariant, CatalogItem, CatalogRequest)
        .outerjoin(CatalogVariant, WishlistItem.catalog_variant_id == CatalogVariant.id)
        .outerjoin(CatalogItem, CatalogVariant.catalog_item_id == CatalogItem.id)
        .outerjoin(CatalogRequest, WishlistItem.catalog_request_id == CatalogRequest.id)
        .where(WishlistItem.user_id == current_user.id)
        .order_by(WishlistItem.priority.desc(), WishlistItem.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if item_status is not None:
        statement = statement.where(WishlistItem.status == item_status)
    if query:
        pattern = f"%{query}%"
        statement = statement.where(
            or_(
                CatalogItem.canonical_title.ilike(pattern),
                CatalogItem.normalized_title.ilike(pattern),
                CatalogVariant.canonical_title.ilike(pattern),
                CatalogVariant.normalized_title.ilike(pattern),
                CatalogRequest.raw_title.ilike(pattern),
            ),
        )

    rows = await session.execute(statement)
    return [
        _wishlist_detail_schema(
            item=item,
            variant=variant,
            catalog_item=catalog_item,
            catalog_request=catalog_request,
        )
        for item, variant, catalog_item, catalog_request in rows.all()
    ]


@router.post("", response_model=WishlistItemResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_wishlist_item(
    payload: WishlistItemCreateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> WishlistItemResponseSchema:
    service = WishlistService(session)
    item = await service.create_item(
        user=current_user,
        command=CreateWishlistItemCommand(
            catalog_variant_id=payload.catalog_variant_id,
            catalog_request_id=payload.catalog_request_id,
            target_price=payload.target_price,
            currency=payload.currency,
            source_url=str(payload.source_url) if payload.source_url is not None else None,
            priority=payload.priority,
            comment=payload.comment,
        ),
    )
    await session.refresh(item)
    return WishlistItemResponseSchema.model_validate(item)


@router.get("/{item_id}", response_model=WishlistItemResponseSchema)
async def get_wishlist_item(
    item_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> WishlistItemResponseSchema:
    service = WishlistService(session)
    item = await service.get_item(user=current_user, item_id=item_id)
    return WishlistItemResponseSchema.model_validate(item)


@router.patch("/{item_id}", response_model=WishlistItemResponseSchema)
async def update_wishlist_item(
    item_id: UUID,
    payload: WishlistItemUpdateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> WishlistItemResponseSchema:
    service = WishlistService(session)
    item = await service.update_item(
        user=current_user,
        item_id=item_id,
        command=UpdateWishlistItemCommand(
            target_price=payload.target_price,
            currency=payload.currency,
            source_url=str(payload.source_url) if payload.source_url is not None else None,
            priority=payload.priority,
            status=payload.status,
            comment=payload.comment,
        ),
    )
    await session.refresh(item)
    return WishlistItemResponseSchema.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist_item(
    item_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> Response:
    service = WishlistService(session)
    await service.delete_item(user=current_user, item_id=item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _wishlist_detail_schema(
    *,
    item: WishlistItem,
    variant: CatalogVariant | None,
    catalog_item: CatalogItem | None,
    catalog_request: CatalogRequest | None,
) -> WishlistItemDetailedResponseSchema:
    item_title = (
        catalog_item.canonical_title
        if catalog_item is not None
        else catalog_request.raw_title
        if catalog_request is not None
        else "Предмет"
    )
    return WishlistItemDetailedResponseSchema(
        id=item.id,
        user_id=item.user_id,
        catalog_variant_id=item.catalog_variant_id,
        catalog_request_id=item.catalog_request_id,
        catalog_item_id=catalog_item.id if catalog_item is not None else None,
        item_title=item_title,
        variant_title=variant.canonical_title if variant is not None else None,
        variant_label=(
            _variant_label(item_title=item_title, variant=variant) if variant is not None else None
        ),
        target_price=item.target_price,
        currency=item.currency,
        source_url=item.source_url,
        priority=item.priority,
        status=item.status,
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
