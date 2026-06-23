from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db_session
from app.models.user import User
from app.schemas.wishlist import (
    WishlistItemCreateSchema,
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
