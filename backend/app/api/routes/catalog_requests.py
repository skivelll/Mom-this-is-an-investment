from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.exceptions import ForbiddenError, NotFoundError
from app.db.session import get_db_session
from app.models.request import CatalogRequestStatus
from app.models.user import User
from app.repositories.moderation import CatalogRequestRepository
from app.schemas.catalog_requests import (
    CatalogItemDraftSchema,
    CatalogRequestApproveSchema,
    CatalogRequestCreateResponseSchema,
    CatalogRequestCreateSchema,
    CatalogRequestDuplicateSchema,
    CatalogRequestRejectSchema,
    CatalogRequestResponseSchema,
    CatalogVariantDraftSchema,
    WishlistDraftSchema,
    WishlistItemResponseSchema,
)
from app.services.catalog_requests import (
    ApproveCatalogRequestCommand,
    CatalogItemDraft,
    CatalogRequestService,
    CatalogVariantDraft,
    CreateCatalogRequestCommand,
    MarkDuplicateCatalogRequestCommand,
    RejectCatalogRequestCommand,
    WishlistDraft,
)

router = APIRouter(prefix="/catalog-requests", tags=["catalog requests"])
moderation_router = APIRouter(
    prefix="/moderation/catalog-requests",
    tags=["catalog request moderation"],
)

CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "",
    response_model=CatalogRequestCreateResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_catalog_request(
    payload: CatalogRequestCreateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CatalogRequestCreateResponseSchema:
    service = CatalogRequestService(session)
    created = await service.create_request(
        user=current_user,
        command=CreateCatalogRequestCommand(
            category_id=payload.category_id,
            raw_title=payload.raw_title,
            description=payload.description,
            source_url=str(payload.source_url) if payload.source_url is not None else None,
            proposed_data=payload.proposed_data,
            wishlist=_to_wishlist_draft(payload.wishlist),
        ),
    )
    return CatalogRequestCreateResponseSchema(
        request=CatalogRequestResponseSchema.model_validate(created.request),
        wishlist_item=(
            WishlistItemResponseSchema.model_validate(created.wishlist_item)
            if created.wishlist_item is not None
            else None
        ),
    )


@router.get("", response_model=list[CatalogRequestResponseSchema])
async def list_my_catalog_requests(
    current_user: CurrentUser,
    session: DbSession,
    request_status: Annotated[CatalogRequestStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CatalogRequestResponseSchema]:
    repository = CatalogRequestRepository(session)
    requests = await repository.list_for_user(
        user_id=current_user.id,
        status=request_status,
        limit=limit,
        offset=offset,
    )
    return [CatalogRequestResponseSchema.model_validate(request) for request in requests]


@router.get("/{request_id}", response_model=CatalogRequestResponseSchema)
async def get_my_catalog_request(
    request_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> CatalogRequestResponseSchema:
    repository = CatalogRequestRepository(session)
    request = await repository.get_by_id_for_user(
        request_id=request_id,
        user_id=current_user.id,
    )
    if request is None:
        raise NotFoundError("Catalog request was not found.")
    return CatalogRequestResponseSchema.model_validate(request)


@moderation_router.get("", response_model=list[CatalogRequestResponseSchema])
async def list_moderation_queue(
    current_user: CurrentUser,
    session: DbSession,
    request_status: Annotated[CatalogRequestStatus | None, Query(alias="status")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[CatalogRequestResponseSchema]:
    _ensure_moderator(current_user)
    repository = CatalogRequestRepository(session)
    requests = await repository.list_queue(
        status=request_status,
        limit=limit,
        offset=offset,
    )
    return [CatalogRequestResponseSchema.model_validate(request) for request in requests]


@moderation_router.get("/{request_id}", response_model=CatalogRequestResponseSchema)
async def get_moderation_request(
    request_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
) -> CatalogRequestResponseSchema:
    _ensure_moderator(current_user)
    repository = CatalogRequestRepository(session)
    request = await repository.get_by_id(request_id)
    if request is None:
        raise NotFoundError("Catalog request was not found.")
    return CatalogRequestResponseSchema.model_validate(request)


@moderation_router.post("/{request_id}/approve", response_model=CatalogRequestResponseSchema)
async def approve_catalog_request(
    request_id: UUID,
    payload: CatalogRequestApproveSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CatalogRequestResponseSchema:
    service = CatalogRequestService(session)
    request = await service.approve_request(
        moderator=current_user,
        command=ApproveCatalogRequestCommand(
            request_id=request_id,
            existing_catalog_item_id=payload.existing_catalog_item_id,
            existing_variant_id=payload.existing_variant_id,
            new_catalog_item=_to_item_draft(payload.new_catalog_item),
            new_variant=_to_variant_draft(payload.new_variant),
            comment=payload.comment,
            payload=payload.payload,
        ),
    )
    await session.refresh(request)
    return CatalogRequestResponseSchema.model_validate(request)


@moderation_router.post("/{request_id}/reject", response_model=CatalogRequestResponseSchema)
async def reject_catalog_request(
    request_id: UUID,
    payload: CatalogRequestRejectSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CatalogRequestResponseSchema:
    service = CatalogRequestService(session)
    request = await service.reject_request(
        moderator=current_user,
        command=RejectCatalogRequestCommand(
            request_id=request_id,
            reason=payload.reason,
            comment=payload.comment,
            payload=payload.payload,
        ),
    )
    await session.refresh(request)
    return CatalogRequestResponseSchema.model_validate(request)


@moderation_router.post("/{request_id}/duplicate", response_model=CatalogRequestResponseSchema)
async def mark_catalog_request_duplicate(
    request_id: UUID,
    payload: CatalogRequestDuplicateSchema,
    current_user: CurrentUser,
    session: DbSession,
) -> CatalogRequestResponseSchema:
    service = CatalogRequestService(session)
    request = await service.mark_duplicate(
        moderator=current_user,
        command=MarkDuplicateCatalogRequestCommand(
            request_id=request_id,
            existing_variant_id=payload.existing_variant_id,
            comment=payload.comment,
            payload=payload.payload,
        ),
    )
    await session.refresh(request)
    return CatalogRequestResponseSchema.model_validate(request)


def _to_wishlist_draft(payload: WishlistDraftSchema | None) -> WishlistDraft | None:
    if payload is None:
        return None
    return WishlistDraft(
        target_price=payload.target_price,
        currency=payload.currency,
        source_url=str(payload.source_url) if payload.source_url is not None else None,
        priority=payload.priority,
        comment=payload.comment,
    )


def _to_item_draft(payload: CatalogItemDraftSchema | None) -> CatalogItemDraft | None:
    if payload is None:
        return None
    return CatalogItemDraft(
        category_id=payload.category_id,
        canonical_title=payload.canonical_title,
        normalized_title=payload.normalized_title,
        description=payload.description,
        release_year=payload.release_year,
        status=payload.status,
    )


def _to_variant_draft(payload: CatalogVariantDraftSchema | None) -> CatalogVariantDraft | None:
    if payload is None:
        return None
    return CatalogVariantDraft(
        canonical_title=payload.canonical_title,
        normalized_title=payload.normalized_title,
        sku=payload.sku,
        barcode=payload.barcode,
        release_date=payload.release_date,
        status=payload.status,
    )


def _ensure_moderator(user: User) -> None:
    if user.role.value not in {"moderator", "senior_moderator", "admin"}:
        raise ForbiddenError("Moderator permissions are required.")
